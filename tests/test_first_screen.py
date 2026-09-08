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


def test_an_emphasised_first_word_is_not_a_list_bullet():
    # sharkdp/fd 초기 README 4~5번째 줄. `*fd* is a ...`를 목록 항목으로 읽으면
    # 한 줄 정의를 통째로 건너뛰고 뒤 문단을 정의로 잡는다.
    text = ("# fd\n"
            "[![Build Status](https://travis-ci.org/sharkdp/fd.svg)](https://travis-ci.org/sharkdp/fd)\n"
            "\n"
            "*fd* is a simple, fast and user-friendly alternative to\n"
            "[*find*](https://www.gnu.org/software/findutils/).\n"
            "\n"
            "While it does not seek to mirror all of *find*'s functionality, it provides\n"
            "sensible defaults.\n")

    ol = first_screen.analyze(text).one_liner

    assert ol.line == 4
    assert ol.alternatives == ["find"]


def test_a_tagline_inside_a_centered_html_header_is_the_one_liner():
    # sharkdp/bat 초기 README. 인기 레포가 흔히 쓰는 형태로, <p align="center"> 안에
    # 로고·배지와 함께 한 문장이 들어 있다. 태그만 보고 건너뛰면 정의를 놓친다.
    text = ('<p align="center">\n'
            '  <img src="doc/logo-header.svg" alt="bat - a cat clone with wings"><br>\n'
            '  <img src="https://img.shields.io/crates/l/bat.svg" alt="license">\n'
            '  A <i>cat(1)</i> clone with syntax highlighting and Git integration.\n'
            '</p>\n'
            '\n'
            '<p align="center">\n'
            '  <a href="#installation">Installation</a>\n'
            '</p>\n')

    ol = first_screen.analyze(text).one_liner

    assert ol.text == "A cat(1) clone with syntax highlighting and Git integration."
    assert ol.alternatives == ["cat(1)"]


def test_a_block_introduced_as_the_expected_output_is_result_evidence():
    # 프롬프트 기호가 없어도, 바로 앞 문장이 이게 나올 결과라고 말하면 증거다.
    text = ("# t\n\nA thing.\n\n"
            "Expected output:\n\n"
            '```json\n{"ok": true}\n```\n')

    fs = first_screen.analyze(text)

    assert [(e.kind, e.line) for e in fs.evidence] == [("output_block", 7)]
