"""첫 화면이 방문자의 세 질문에 주는 관찰 가능한 답. 기대값은 픽스처를 직접 읽어 센 것이다."""
from conftest import fixture_text

from showcase import first_screen


def test_one_liner_is_the_first_prose_paragraph_after_the_title():
    # synthetic_early_classic.md 3번째 줄. 초기 고전의 한 줄 설명은 방문자가
    # 아는 도구(`find`)에 자신을 연결한다.
    fs = first_screen.analyze(fixture_text("synthetic_early_classic.md"))

    assert fs.one_liner.line == 3
    assert fs.one_liner.length == 37
    assert fs.one_liner.alternatives == ["find"]


def test_one_liner_skips_the_badge_line_and_measures_the_wrapped_paragraph():
    # synthetic_low_traction.md: 3번째 줄은 배지, 한 줄 정의는 5~9번째 줄에
    # 걸쳐 접힌 280자 문단이고 아는 도구에 연결하지 않는다
    # (sed -n '5,9p' | tr '\n' ' ' | wc -c = 280).
    fs = first_screen.analyze(fixture_text("synthetic_low_traction.md"))

    assert fs.one_liner.line == 5
    assert fs.one_liner.length == 280
    assert fs.one_liner.alternatives == []


def test_one_liner_works_in_korean():
    # tjdwls101010/Ultra-Search 3번째 줄, 121자.
    fs = first_screen.analyze(fixture_text("tjdwls101010__Ultra-Search.md"))

    assert fs.one_liner.line == 3
    assert fs.one_liner.length == 121


def test_result_evidence_is_classified_by_what_it_shows():
    # synthetic_early_classic.md: 5번째 줄 데모 GIF, 21번째 줄 블록은 명령과
    # 그 출력을 함께 보여준다. 배지는 증거로 세지 않는다.
    fs = first_screen.analyze(fixture_text("synthetic_early_classic.md"))

    assert [(e.kind, e.line) for e in fs.evidence] == [("gif", 5), ("output_block", 21)]


def test_a_repo_with_only_a_badge_and_a_diagram_has_no_result_evidence():
    # 저관심 코퍼스에서 가장 자주 나온 형태: 구조는 설명하지만 결과는 보여주지 않는다.
    fs = first_screen.analyze(fixture_text("synthetic_low_traction.md"))

    assert fs.evidence == []


def test_start_path_records_prerequisite_command_and_expected_result():
    # synthetic_early_classic.md: 13번째 줄 전제조건, 15번째 줄 설치 명령,
    # 21번째 줄 첫 실행과 그 출력. 설치 완료가 아니라 첫 성공까지 이어진다.
    sp = first_screen.analyze(fixture_text("synthetic_early_classic.md")).start_path

    assert sp.prereq_lines == [13]
    assert sp.command_lines == [15, 21]
    assert sp.expected_result_lines == [21]


def test_a_blocking_prerequisite_stated_after_the_install_command_is_recorded_as_such():
    # synthetic_low_traction.md: 설치 명령은 39번째 줄인데 도입을 막는 조건
    # (계정·관리자 승인)은 44번째 줄에 있다. 위치가 판정의 근거다.
    sp = first_screen.analyze(fixture_text("synthetic_low_traction.md")).start_path

    assert sp.command_lines == [39]
    assert sp.prereq_lines == [44]
    assert sp.expected_result_lines == []
