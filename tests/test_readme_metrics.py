"""README 텍스트 → 구조 지표. 기대값은 픽스처 파일을 직접 읽어 센 줄 번호다."""
from conftest import fixture_text

from showcase import readme_metrics


def test_install_heading_found_when_written_in_korean():
    # tjdwls101010/Ultra-Search: "## 설치"가 17번째 줄. 수집 단계 스크립트는
    # 영어 헤딩만 봐서 이걸 놓쳤다(코덱스 발견 버그 a).
    m = readme_metrics.analyze(fixture_text("tjdwls101010__Ultra-Search.md"))

    assert m.install_heading_line == 17


def test_mermaid_fence_is_not_the_first_code_block():
    # synthetic_low_traction.md: 12번째 줄이 ```mermaid, 31번째 줄이 ```yaml.
    # 다이어그램은 실행할 수 있는 명령이 아니므로 첫 코드 줄이 아니다
    # (코덱스 발견 버그 b). 설정 예제인 yaml은 코드로 센다.
    m = readme_metrics.analyze(fixture_text("synthetic_low_traction.md"))

    assert m.first_code_line == 31
    assert [c.lang for c in m.code_blocks] == ["yaml", "bash"]


def test_badge_is_not_counted_as_result_evidence():
    # 배지·로고와 "결과를 보여주는 이미지"는 방문자에게 다른 답을 준다.
    # synthetic_low_traction.md의 3번째 줄은 shields.io 배지뿐이다.
    m = readme_metrics.analyze(fixture_text("synthetic_low_traction.md"))

    assert m.badges == 1
    assert m.first_result_image_line is None


def test_demo_gif_counts_as_a_result_image():
    # synthetic_early_classic.md의 5번째 줄은 실행 결과를 담은 GIF다.
    m = readme_metrics.analyze(fixture_text("synthetic_early_classic.md"))

    assert m.badges == 0
    assert m.first_result_image_line == 5


def test_headings_inside_a_code_block_are_not_headings():
    text = "# Real\n\n```bash\n# not a heading\necho hi\n```\n\n## Also real\n"

    m = readme_metrics.analyze(text)

    assert [(h.line, h.text) for h in m.headings] == [(1, "Real"), (8, "Also real")]
