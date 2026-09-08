"""유사 프로젝트 후보. 검색어 조합·결과 정규화·Similar 절 탐지."""
from conftest import fixture_text

from showcase import similar


def test_query_drops_filler_words_that_match_every_tool():
    # 한 줄 정의를 그대로 넣으면 검색이 흐려진다. "a"·"to" 같은 불용어와,
    # 뜻은 있지만 거의 모든 도구에 붙는 "simple"을 함께 뺀다.
    q = similar.build_query("A simple, fast alternative to `find`", topics=["cli", "rust"])

    assert q == "fast alternative find topic:cli topic:rust"


def test_query_keeps_filler_words_when_nothing_else_is_left():
    # 정체성 낱말이 2개 미만이면 불용어 제거가 검색어 자체를 없앤다.
    assert similar.build_query("A simple thing") == "simple thing"


def test_results_are_normalized_to_the_fields_the_interview_needs():
    # gh search repos는 topics를 주지 않는다. 없으면 빈 목록으로 두고 따로 채운다.
    raw = [{
        "fullName": "sharkdp/fd", "stargazersCount": 44337,
        "description": "A simple, fast and user-friendly alternative to 'find'",
        "pushedAt": "2026-09-01T00:00:00Z",
        "license": {"key": "apache-2.0"}, "homepage": "",
    }]

    got = similar.normalize(raw)

    assert got[0]["repo"] == "sharkdp/fd"
    assert got[0]["stars"] == 44337
    assert got[0]["topics"] == []
    assert got[0]["license"] == "apache-2.0"
    assert got[0]["pushed_at"] == "2026-09-01"


def test_topics_are_fetched_per_candidate_because_search_does_not_return_them():
    calls = []

    def runner(args):
        calls.append(args)
        if args[0] == "search":
            return '[{"fullName": "o/r", "stargazersCount": 1, "pushedAt": "2026-01-01T00:00:00Z"}]'
        return '["cli", "rust"]'

    got = similar.search("q", runner=runner)

    assert got[0]["topics"] == ["cli", "rust"]
    assert calls[1][:2] == ["api", "repos/o/r"]


def test_a_repo_untouched_for_over_a_year_sorts_below_a_smaller_active_one():
    cands = [
        {"repo": "old/big", "stars": 9000, "pushed_at": "2024-01-01"},
        {"repo": "new/small", "stars": 12, "pushed_at": "2026-08-01"},
    ]

    ranked = similar.rank(cands, today="2026-09-08")

    assert [c["repo"] for c in ranked] == ["new/small", "old/big"]


def test_similar_projects_section_is_found_with_its_line():
    text = "# t\n\nA thing.\n\n## Alternatives\n\n- other\n"

    assert similar.find_similar_section(text) == (5, "Alternatives")


def test_a_readme_without_such_a_section_reports_none():
    assert similar.find_similar_section(fixture_text("synthetic_low_traction.md")) is None
