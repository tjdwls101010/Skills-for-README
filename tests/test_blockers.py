"""채택을 막는 결손 판정. 상태는 present/absent/lookup_failed/undetermined 넷이다."""
from conftest import fixture_text

from showcase import blockers
from showcase.github import RepoFacts


def find(findings, blocker_id):
    return next(f for f in findings if f.id == blocker_id)


def test_readme_claims_a_license_that_no_file_backs():
    # vibe-toolkit 패턴: 본문은 MIT라고 쓰지만 파일이 감지되지 않는다.
    facts = RepoFacts(license_key=None, has_license_file=False)

    fs = blockers.analyze(fixture_text("synthetic_low_traction.md"), facts)

    mismatch = find(fs, "license_mismatch")
    assert mismatch.state == "present"
    assert mismatch.evidence[0].line == 54
    assert "MIT" in mismatch.evidence[0].text


def test_license_file_and_readme_agreeing_is_not_a_blocker():
    facts = RepoFacts(license_key="mit", has_license_file=True)

    fs = blockers.analyze(fixture_text("synthetic_early_classic.md"), facts)

    assert find(fs, "license_missing").state == "absent"


def test_license_state_is_lookup_failed_when_the_repo_was_never_queried():
    # --offline이면 원격 메타데이터를 모른다. "없음"과 "확인 못 함"은 다른 답이다.
    facts = RepoFacts()  # 모든 필드가 미조회

    fs = blockers.analyze(fixture_text("synthetic_early_classic.md"), facts)

    assert find(fs, "license_missing").state == "lookup_failed"


def test_a_start_path_that_only_works_on_the_owners_machine():
    # CCC 패턴: 명령이 사설 IP와 소유자 홈 경로를 전제한다. 외부인은 재현할 수 없다.
    fs = blockers.analyze(fixture_text("synthetic_contradiction.md"), RepoFacts())

    start = find(fs, "start_path_unreproducible")
    assert start.state == "present"
    assert [e.line for e in start.evidence] == [18]
    assert "192.168.3.116" in start.evidence[0].text


def test_a_feature_used_as_an_example_and_listed_as_planned_stops_the_reader():
    # autoflow·mcp-re 패턴: 9번째 줄 예제의 email 싱크가 23번째 줄에서는 예정 기능이다.
    fs = blockers.analyze(fixture_text("synthetic_contradiction.md"), RepoFacts())

    clash = find(fs, "status_contradiction")
    assert clash.state == "present"
    assert [e.line for e in clash.evidence] == [9, 23]


def test_a_roadmap_of_features_never_used_as_examples_is_not_a_contradiction():
    fs = blockers.analyze(fixture_text("synthetic_low_traction.md"), RepoFacts())

    assert find(fs, "status_contradiction").state == "absent"


def test_a_prerequisite_stated_before_the_first_command_is_not_a_blocker():
    fs = blockers.analyze(fixture_text("synthetic_early_classic.md"), RepoFacts())

    assert find(fs, "prereq_unstated").state == "absent"


def test_a_prerequisite_that_only_appears_after_the_install_command_needs_a_human():
    # mcp-ms-loop 패턴. 스크립트는 위치만 안다. 그 조건이 도입을 막는지는 읽어야 안다.
    fs = blockers.analyze(fixture_text("synthetic_low_traction.md"), RepoFacts())

    prereq = find(fs, "prereq_unstated")
    assert prereq.state == "undetermined"
    assert [e.line for e in prereq.evidence] == [44]


def test_no_prerequisite_sentence_anywhere_is_a_blocker():
    text = "# t\n\nA thing.\n\n## Install\n\n```bash\nnpm i -g t\n```\n"

    fs = blockers.analyze(text, RepoFacts())

    assert find(fs, "prereq_unstated").state == "present"
