"""판정을 사람용/JSON으로 낸다. 점수는 내지 않는다.

묶음이 둘인 이유: 채택을 막는 결손은 소개가 아무리 좋아도 방문자를 돌려보내고,
설득력 개선은 결손이 없을 때만 실제로 읽힌다."""
from __future__ import annotations

from dataclasses import asdict

from . import blockers, first_screen, readme_metrics
from .github import RepoFacts

PERSUASION_ORDER = ("one_liner", "result_evidence", "start_path", "description",
                    "topics", "homepage", "releases", "social_preview")


def _line(l) -> dict:
    return {"line": l.line, "text": l.text}


def build(facts: RepoFacts, fetched: str, compare: dict | None = None) -> dict:
    text = facts.readme_text or ""
    m = readme_metrics.analyze(text)
    fs = first_screen.analyze(text)
    # README가 비어 있어도 판정한다 — 라이선스는 파일에서 오고, README에서 오는
    # 항목은 자연히 "없음"이 된다. 여기서 멈추면 README를 처음 쓰는 레포가
    # 아무 판정도 받지 못한다.
    found = blockers.analyze(text, facts)

    return {
        "target": facts.target,
        "fetched": fetched,
        "readme_path": facts.readme_path,
        "blockers": [
            {"id": f.id, "state": f.state,
             "evidence": [_line(e) for e in f.evidence], "note": f.note}
            for f in found
        ],
        "persuasion": _persuasion(facts, m, fs),
        "metrics": {
            "lines": m.lines,
            "words": m.words,
            "badges": m.badges,
            "first_result_image_line": m.first_result_image_line,
            "first_code_line": m.first_code_line,
            "install_heading_line": m.install_heading_line,
            "one_liner_line": fs.one_liner.line if fs.one_liner else None,
            "one_liner_len": fs.one_liner.length if fs.one_liner else None,
            "evidence_types": sorted({e.kind for e in fs.evidence}),
        },
        "compare": compare,
        "errors": facts.errors,
    }


def _state(value) -> str:
    if value is None:
        return blockers.LOOKUP_FAILED
    return blockers.PRESENT if value else blockers.ABSENT


def _persuasion(facts: RepoFacts, m, fs) -> list[dict]:
    out = []

    def add(pid, state, value=None, evidence=(), note=""):
        out.append({"id": pid, "state": state, "value": value,
                    "evidence": [_line(e) for e in evidence], "note": note})

    if fs.one_liner:
        add("one_liner", blockers.PRESENT, fs.one_liner.length,
            [blockers.Line(fs.one_liner.line, fs.one_liner.text)],
            "아는 작업·대안에 연결하는가는 문장을 읽고 판정한다."
            if not fs.one_liner.alternatives
            else f"대안 언급: {', '.join(fs.one_liner.alternatives)}")
    else:
        add("one_liner", blockers.ABSENT, None, (),
            "제목 다음에 산문 문단이 없다. 방문자가 재진술할 문장이 없다.")

    kinds = sorted({e.kind for e in fs.evidence})
    add("result_evidence", blockers.PRESENT if kinds else blockers.ABSENT, kinds,
        [blockers.Line(e.line, f"{e.kind}: {e.text[:80]}") for e in fs.evidence])

    sp = fs.start_path
    complete = bool(sp.command_lines and sp.expected_result_lines)
    add("start_path", blockers.PRESENT if complete else blockers.ABSENT,
        {"prereq_lines": sp.prereq_lines, "command_lines": sp.command_lines,
         "expected_result_lines": sp.expected_result_lines},
        (), "" if complete else "설치 명령은 있으나 첫 실행의 예상 결과가 없다."
        if sp.command_lines else "실행 명령이 없다.")

    add("description", _state(facts.description if facts.description is not None else None),
        facts.description, (),
        _description_note(facts.description))
    add("topics", _state(facts.topics if facts.topics is not None else None), facts.topics)
    add("homepage", _state(facts.homepage if facts.homepage is not None else None), facts.homepage)
    add("releases", blockers.LOOKUP_FAILED if facts.releases_count is None
        else (blockers.PRESENT if facts.releases_count else blockers.ABSENT),
        facts.releases_count)
    add("social_preview",
        blockers.LOOKUP_FAILED if facts.social_preview is None
        else (blockers.PRESENT if facts.social_preview else blockers.ABSENT),
        facts.social_preview, (),
        "" if facts.social_preview is not None
        else "GraphQL로 확인하지 못했다(오프라인이거나 권한 없음).")
    order = {p: i for i, p in enumerate(PERSUASION_ORDER)}
    return sorted(out, key=lambda p: order.get(p["id"], 99))


def _description_note(desc: str | None) -> str:
    if desc is None:
        return "조회하지 않았다."
    if not desc:
        return "비어 있다. 검색 결과와 프로필 목록에서 레포가 자기를 설명할 기회가 사라진다."
    n = len(" ".join(desc.split()))
    if n > 137:
        return (f"{n}자. 검색 결과에서는 137자에서 단어 중간이라도 잘리고 `…`이 붙는다. "
                "앞 137자 안에 정체성이 끝나는지 본다.")
    return f"{n}자. 검색 결과에서 잘리지 않는다."


def render_text(report: dict) -> str:
    L = []
    L.append(f"대상: {report['target']}   조회: {report['fetched']}")
    if report.get("readme_path"):
        L.append(f"README: {report['readme_path']}")
    L.append("")
    L.append("## 채택을 막는 결손")
    L.append("")
    for f in report["blockers"]:
        L.append(f"[{f['state']:<13}] {f['id']}")
        if f["note"]:
            L.append(f"                {f['note']}")
        # absent는 "확인했고 문제가 아니다"이다. 근거 줄을 함께 찍으면 그 줄이
        # 문제인 것처럼 읽힌다. JSON에는 그대로 남는다.
        if f["state"] != blockers.ABSENT:
            for e in f["evidence"][:4]:
                L.append(f"                {e['line']:>4}: {e['text'][:96]}")
    L.append("")
    L.append("## 설득력 개선")
    L.append("")
    for p in report["persuasion"]:
        val = "" if p["value"] in (None, "", [], {}) else f"  {p['value']}"
        L.append(f"[{p['state']:<13}] {p['id']}{str(val)[:110]}")
        if p["note"]:
            L.append(f"                {p['note']}")
        for e in p["evidence"][:3]:
            L.append(f"                {e['line']:>4}: {e['text'][:96]}")
    m = report["metrics"]
    L.append("")
    L.append("## 구조 지표 (합격점 없음. 개선 전후 비교에만 쓴다)")
    L.append("")
    L.append("  " + "  ".join(f"{k}={v}" for k, v in m.items()))
    if report.get("compare"):
        c = report["compare"]
        L.append("")
        L.append(f"## 비교 대상 {c.get('repo')}")
        L.append(f"  description: {c.get('description')}")
        L.append(f"  topics: {c.get('topics')}")
        L.append(f"  공유 topic: {c.get('shared_topics')}")
        L.append(f"  없는 topic: {c.get('missing_topics')}")
    if report.get("errors"):
        L.append("")
        L.append("## 조회 실패 (없음이 아니라 모름)")
        for e in report["errors"]:
            L.append(f"  - {e}")
    return "\n".join(L)
