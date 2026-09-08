"""가장 가까운 대안 레포 후보를 찾는다.

찾은 레포는 (1) topics·description 어휘 정렬, (2) 조건과 손해를 포함한 비교표,
(3) 한 줄 정의의 앵커, (4) "Similar projects" 절 추가를 제안할 PR 후보에 쓴다.
스타게이저·기여자 등 사람 정보는 조회하지 않는다."""
from __future__ import annotations

import datetime as _dt
import json
import re

from . import readme_metrics
from .github import GhError, run_gh

# 검색을 흐리는 낱말. 한 줄 정의에 거의 항상 있고 후보를 좁히지 못한다.
STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "to", "of", "in", "on", "with", "your",
    "you", "it", "is", "are", "that", "this", "very", "just", "can", "will",
    "simple",  # 남기면 "simple"만으로 수만 개가 걸린다 — 아래 주석 참고
}
# "simple"은 뜻이 있는 낱말이지만 검색어로는 거의 모든 도구에 붙는다. 후보의
# 정밀도가 검색 결과 수보다 중요해 뺀다. 대상 레포의 정체성 낱말이 2개 미만이
# 남으면 build_query가 불용어 제거를 포기한다.

SIMILAR_HEADINGS = (
    "similar", "alternatives", "alternative", "comparison", "compared",
    "related projects", "related work", "prior art", "see also",
    "비교", "대안", "관련",
)


def build_query(one_liner: str, topics: list[str] | None = None,
                language: str | None = None) -> str:
    words = [w for w in re.findall(r"[A-Za-z][A-Za-z0-9+.#-]*", one_liner.lower())]
    kept = [w for w in words if w not in STOPWORDS and len(w) > 2]
    if len(kept) < 2:
        kept = [w for w in words if len(w) > 2]
    parts = kept[:6]
    parts += [f"topic:{t}" for t in (topics or [])]
    if language:
        parts.append(f"language:{language}")
    return " ".join(parts)


def normalize(raw: list[dict]) -> list[dict]:
    out = []
    for r in raw:
        topics = r.get("topics")
        if topics is None:
            topics = [t.get("name") for t in (r.get("repositoryTopics") or []) if t.get("name")]
        lic = r.get("license") or {}
        out.append({
            "repo": r.get("fullName") or r.get("full_name") or "",
            "stars": r.get("stargazersCount") or r.get("stargazers_count") or 0,
            "description": r.get("description") or "",
            "topics": topics,
            "pushed_at": (r.get("pushedAt") or r.get("pushed_at") or "")[:10],
            "license": lic.get("key") or lic.get("spdx_id") or "",
            "homepage": r.get("homepage") or "",
        })
    return out


def rank(candidates: list[dict], today: str | None = None) -> list[dict]:
    """스타 내림차순. 단 1년 이상 갱신되지 않은 레포는 뒤로 보낸다 —
    죽은 프로젝트를 '가장 가까운 대안'으로 골라 비교표에 쓰면 오래된 정보를 굳힌다."""
    now = _dt.date.fromisoformat(today) if today else _dt.date.today()
    cutoff = now - _dt.timedelta(days=365)

    def stale(c):
        try:
            return _dt.date.fromisoformat((c.get("pushed_at") or "")[:10]) < cutoff
        except ValueError:
            return True

    return sorted(candidates, key=lambda c: (stale(c), -(c.get("stars") or 0)))


def find_similar_section(text: str) -> tuple[int, str] | None:
    for h in readme_metrics.parse_headings(text):
        t = h.text.lower()
        if any(w in t for w in SIMILAR_HEADINGS):
            return (h.line, h.text)
    return None


# `gh search repos`는 topics를 주지 않는다. 어휘 정렬이 이 스크립트의 주 용도라
# 후보마다 한 번 더 물어 채운다 — limit만큼만 부르므로 기본 10회다.
SEARCH_FIELDS = "fullName,stargazersCount,description,pushedAt,license,homepage"


def search(query: str, limit: int = 10, runner=run_gh) -> list[dict]:
    args = ["search", "repos", query, "--limit", str(limit), "--json", SEARCH_FIELDS]
    found = normalize(json.loads(runner(args)))
    for c in found:
        c["topics"] = fetch_topics(c["repo"], runner)
    return found


def fetch_topics(repo: str, runner=run_gh) -> list[str]:
    try:
        return json.loads(runner(["api", f"repos/{repo}", "--jq", ".topics"])) or []
    except (GhError, ValueError):
        return []
