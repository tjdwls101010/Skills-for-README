"""채택을 막는 결손. 설득력 개선보다 먼저 확인한다.

여기서 나오는 건 판정이지 점수가 아니다. 각 판정은 근거가 된 줄을 함께 낸다."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import first_screen, readme_metrics
from .github import RepoFacts

PRESENT = "present"            # 결손이 있다
ABSENT = "absent"              # 확인했고 결손이 아니다
LOOKUP_FAILED = "lookup_failed"  # 조회하지 못해 모른다
UNDETERMINED = "undetermined"  # 자료는 있으나 스크립트가 판정할 수 없다


@dataclass
class Line:
    line: int
    text: str


@dataclass
class Finding:
    id: str
    state: str
    evidence: list[Line] = field(default_factory=list)
    note: str = ""


# README 본문이 라이선스를 주장하는 표현. SPDX 식별자로 정규화해 파일·감지값과 맞춘다.
LICENSE_NAMES = {
    "mit": r"\bMIT\b",
    "apache-2.0": r"\bApache[- ]2(?:\.0)?\b",
    "gpl-3.0": r"\bGPL(?:v| )?3\b|\bGNU General Public License,? version 3\b",
    "gpl-2.0": r"\bGPL(?:v| )?2\b",
    "agpl-3.0": r"\bAGPL(?:v| )?3\b",
    "lgpl-3.0": r"\bLGPL(?:v| )?3\b",
    "bsd-3-clause": r"\bBSD[- ]3[- ]Clause\b",
    "bsd-2-clause": r"\bBSD[- ]2[- ]Clause\b",
    "mpl-2.0": r"\bMPL[- ]2(?:\.0)?\b|\bMozilla Public License 2\b",
    "unlicense": r"\bUnlicense\b",
    "isc": r"\bISC\b",
}


def licenses_claimed_in_readme(text: str) -> list[Line]:
    """본문이 라이선스를 말하는 줄. 배지 URL 안의 표기도 주장으로 센다."""
    out = []
    for i, raw in enumerate(text.splitlines(), start=1):
        for key, pat in LICENSE_NAMES.items():
            if re.search(pat, raw, re.I):
                out.append(Line(i, raw.strip()))
                break
    return out


def _spdx_in(raw: str) -> set[str]:
    return {k for k, pat in LICENSE_NAMES.items() if re.search(pat, raw, re.I)}


def check_license(text: str, facts: RepoFacts) -> list[Finding]:
    claims = licenses_claimed_in_readme(text)
    if facts.has_license_file is None:
        note = "라이선스 파일을 조회하지 않았다. 없다고 단정하지 않는다."
        return [Finding("license_missing", LOOKUP_FAILED, claims, note),
                Finding("license_mismatch", LOOKUP_FAILED, claims, note)]

    missing = Finding(
        "license_missing",
        PRESENT if not facts.has_license_file else ABSENT,
        claims,
        "사용·수정·재배포 조건을 확인할 수 없으면 소개가 좋아도 채택을 보류한다."
        if not facts.has_license_file else "",
    )
    if not facts.has_license_file:
        # 파일이 없는데 본문이 라이선스를 주장하면 불일치이기도 하다.
        mismatch = Finding(
            "license_mismatch",
            PRESENT if claims else ABSENT,
            claims,
            "본문은 라이선스를 말하는데 파일이 없다. 어느 쪽이 사실인지 정해야 한다."
            if claims else "",
        )
        return [missing, mismatch]

    detected = facts.license_key or ""
    claimed = set()
    for c in claims:
        claimed |= _spdx_in(c.text)
    if not detected:
        state, note = UNDETERMINED, "파일은 있으나 GitHub이 식별하지 못했다(NOASSERTION). 본문 설명과 대조해 사람이 판정한다."
    elif not claimed:
        state, note = ABSENT, ""
    elif detected in claimed:
        state, note = ABSENT, ""
    else:
        state, note = PRESENT, f"감지값 {detected}과 본문 주장 {sorted(claimed)}이 다르다."
    return [missing, Finding("license_mismatch", state, claims, note)]


# 명령 안에 있으면 그 명령이 소유자 기계에서만 도는 것. 외부인은 재현하지 못한다.
LOCAL_ONLY_PATTERNS = (
    r"\b(?:10|127)\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
    r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
    r"\b172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}\b",
    r"/Users/(?!<|\$|USER\b|you\b|your\b)[A-Za-z0-9._-]+",
    r"/home/(?!<|\$|USER\b|you\b|your\b)[A-Za-z0-9._-]+",
    r"[Cc]:\\\\?Users\\\\?[A-Za-z0-9._-]+",
)
# 아직 아니라고 말하는 표현.
PLANNED_PATTERNS = (
    r"\bplanned\b", r"\bcoming soon\b", r"\bnot yet\b", r"\bunimplemented\b",
    r"\bnot implemented\b", r"\broadmap\b", r"\bwip\b", r"\btodo\b",
    r"예정", r"미구현", r"아직",
)


def check_start_path(text: str) -> Finding:
    ev = []
    for b in readme_metrics.parse_code_blocks(text):
        for offset, raw in enumerate(b.body.splitlines(), start=1):
            if any(re.search(p, raw) for p in LOCAL_ONLY_PATTERNS):
                ev.append(Line(b.line + offset, raw.strip()))
    if not ev:
        return Finding("start_path_unreproducible", ABSENT)
    return Finding("start_path_unreproducible", PRESENT, ev,
                   "명령이 소유자 기계에만 있는 주소·경로를 전제한다. 자리표시자로 바꾸거나 만드는 법을 적는다.")


def check_status_contradiction(text: str) -> Finding:
    """예정이라고 적힌 기능 이름이 앞선 예제 안에서 이미 쓰이고 있는가."""
    lines = readme_metrics._code_masked_lines(text)
    planned = [(i, raw) for i, raw in enumerate(lines, start=1)
               if any(re.search(p, raw, re.I) for p in PLANNED_PATTERNS)]
    if not planned:
        return Finding("status_contradiction", ABSENT)

    blocks = readme_metrics.parse_code_blocks(text)
    ev = []
    for i, raw in planned:
        for name in _feature_names(raw):
            for b in blocks:
                if b.line < i and re.search(rf"\b{re.escape(name)}\b", b.body, re.I):
                    ev.append(Line(b.line, b.body.splitlines()[0].strip()))
                    ev.append(Line(i, raw.strip()))
                    break
            if ev:
                break
        if ev:
            break
    if not ev:
        return Finding("status_contradiction", ABSENT)
    return Finding("status_contradiction", PRESENT, ev,
                   "예제에서 쓰는 기능이 뒤에서는 예정 기능이다. 모순 하나가 나머지 문서의 신뢰를 멈춘다.")


def _feature_names(raw: str) -> list[str]:
    """예정 항목에서 기능 이름으로 쓸 만한 소문자 낱말. 흔한 낱말은 뺀다."""
    stop = {"planned", "for", "the", "a", "an", "not", "yet", "implemented", "soon",
            "coming", "sink", "support", "and", "or", "in", "to", "roadmap", "wip", "todo"}
    words = re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", raw)
    return [w for w in (x.lower() for x in words) if w not in stop]


def check_prereq(text: str) -> Finding:
    sp = first_screen.find_start_path(text)
    lines = text.splitlines()
    if not sp.command_lines:
        return Finding("prereq_unstated", UNDETERMINED, [],
                       "실행 명령이 없어 전제조건의 필요 여부를 판정할 수 없다.")
    if not sp.prereq_lines:
        return Finding("prereq_unstated", PRESENT, [],
                       "전제조건·요구 권한·비용을 말하는 문장이 없다. 없는 것인지 안 적은 것인지는 소유자만 안다.")
    first_cmd = min(sp.command_lines)
    late = [l for l in sp.prereq_lines if l > first_cmd]
    if late and not [l for l in sp.prereq_lines if l < first_cmd]:
        return Finding("prereq_unstated", UNDETERMINED,
                       [Line(l, lines[l - 1].strip()) for l in late],
                       f"전제조건이 첫 명령({first_cmd}번째 줄)보다 뒤에 있다. "
                       "도입을 막는 조건인지는 내용을 읽고 판정한다.")
    return Finding("prereq_unstated", ABSENT)


def analyze(text: str, facts: RepoFacts) -> list[Finding]:
    return [*check_license(text, facts), check_prereq(text),
            check_start_path(text), check_status_contradiction(text)]
