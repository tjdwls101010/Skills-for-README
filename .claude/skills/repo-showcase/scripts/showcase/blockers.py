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

    if facts.license_key is None:
        # 파일은 봤지만 감지값은 조회하지 않았다(--offline). NOASSERTION과 다르다.
        return [missing, Finding("license_mismatch", LOOKUP_FAILED, claims,
                                 "라이선스 파일은 있으나 감지값을 조회하지 않아 대조하지 못했다.")]

    detected = facts.license_key
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


# 독자가 손으로 바꿔 넣어야 하는 자리. `<DIR>`처럼 낱말 하나짜리 옵션 표기는
# 관례이므로 제외하고, `<this repo>`처럼 공백이 든 산문만 잡는다 — 그건 표기가
# 아니라 "여기에 뭔가를 알아내서 넣어라"는 뜻이고, 첫 명령이 그대로 실패한다.
PLACEHOLDER_PATTERN = r"<[^<>\n]*\s[^<>\n]*>"


def check_start_path(text: str) -> Finding:
    ev, holes = [], []
    for b in readme_metrics.parse_code_blocks(text):
        for offset, raw in enumerate(b.body.splitlines(), start=1):
            if any(re.search(p, raw) for p in LOCAL_ONLY_PATTERNS):
                ev.append(Line(b.line + offset, raw.strip()))
            elif re.search(PLACEHOLDER_PATTERN, raw):
                holes.append(Line(b.line + offset, raw.strip()))
    if ev:
        return Finding("start_path_unreproducible", PRESENT, ev,
                       "명령이 소유자 기계에만 있는 주소·경로를 전제한다. 자리표시자로 바꾸거나 만드는 법을 적는다.")
    if holes:
        return Finding("start_path_unreproducible", UNDETERMINED, holes,
                       "명령에 독자가 채워야 하는 자리가 있다. 사용법 요약이면 괜찮고, "
                       "따라 실행할 첫 명령이면 그대로 실패한다.")
    return Finding("start_path_unreproducible", ABSENT)


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
            if _is_ubiquitous(name, blocks):
                continue
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
    # 낱말이 겹친다는 것이 모순의 증거는 아니다. 이 검사는 읽어 볼 두 곳을
    # 짚어 줄 뿐이고, 모순인지는 두 문장을 읽어야 안다. present로 단정하면
    # 가장 높은 우선순위 묶음에 오탐이 들어간다.
    return Finding("status_contradiction", UNDETERMINED, ev,
                   "예정이라고 적힌 것과 예제가 같은 낱말을 쓴다. 두 곳을 읽고 "
                   "모순인지 판정한다 — 모순이면 하나가 나머지 문서의 신뢰를 멈춘다.")


# 기능 이름이 될 수 없는 낱말. 이걸 걸러내지 않으면 "the one this README gave"의
# `one`이 예제의 "One-time login"과 맞아 없는 모순을 만들어 낸다 — 실제로 그랬다.
_COMMON_WORDS = {
    "planned", "implemented", "soon", "coming", "roadmap", "todo", "sink", "support",
    "about", "after", "again", "all", "also", "and", "any", "are", "back", "because",
    "been", "before", "being", "both", "but", "can", "cannot", "case", "does", "done",
    "down", "each", "even", "every", "example", "first", "for", "found", "from", "gave",
    "gone", "had", "has", "have", "here", "how", "into", "its", "just", "like", "made",
    "make", "many", "more", "most", "much", "must", "need", "new", "next", "nothing",
    "not", "note", "now", "off", "one", "only", "other", "out", "over", "own", "readme",
    "reason", "return", "returns", "same", "see", "she", "should", "since", "some",
    "still", "such", "than", "that", "the", "their", "them", "then", "there", "these",
    "they", "this", "those", "through", "time", "two", "under", "until", "use", "used",
    "uses", "using", "very", "was", "way", "were", "what", "when", "where", "which",
    "while", "who", "why", "will", "with", "without", "would", "yet", "you", "your",
}


def _is_ubiquitous(name: str, blocks) -> bool:
    """예제 대부분에 나오는 낱말은 기능 이름이 아니라 도구 이름이다.
    (레포 이름이 모든 명령의 첫 낱말이라 그대로 두면 항상 걸린다.)"""
    if len(blocks) < 2:
        return False
    hits = sum(1 for b in blocks if re.search(rf"\b{re.escape(name)}\b", b.body, re.I))
    return hits * 2 > len(blocks)


def _feature_names(raw: str) -> list[str]:
    """예정 항목이 가리키는 기능의 이름.

    문장에 나온 모든 낱말이 후보가 아니다. "`likers` is planned. Use agentic-x
    search instead."에서 예정된 것은 `likers`이고 `search`는 우회 방법이다.
    그래서 백틱이 있으면 그것만 믿고, 없으면 첫 후보 하나만 쓴다."""
    backticked = [w.lower() for w in re.findall(r"`([A-Za-z][\w.-]*)`", raw)]
    if backticked:
        return backticked
    words = [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z0-9_-]{3,}", raw)]
    rest = [w for w in words if w not in _COMMON_WORDS]
    return rest[:1]


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
