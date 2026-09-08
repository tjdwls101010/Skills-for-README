"""커뮤니티 파일 생성. 기존 파일을 덮어쓰지 않고, 라이선스를 임의로 고르지 않는다."""
import subprocess
import sys
from pathlib import Path

SCAFFOLD = (Path(__file__).resolve().parents[1] / ".claude" / "skills" /
            "repo-showcase" / "scripts" / "scaffold_community.py")


def run(*args, cwd=None):
    return subprocess.run([sys.executable, str(SCAFFOLD), *args],
                          capture_output=True, text=True, cwd=cwd)


def test_license_needs_an_explicit_choice(tmp_path):
    # 소유자가 고르지 않은 라이선스를 스크립트가 정하면 권리관계를 대신 결정하는 것이 된다.
    r = run("--file", "license", "--out", str(tmp_path))

    assert r.returncode == 2
    assert list(tmp_path.iterdir()) == []


def test_an_existing_file_is_never_overwritten(tmp_path):
    (tmp_path / "LICENSE").write_text("기존 내용\n")

    r = run("--file", "license", "--license", "mit", "--holder", "S", "--out", str(tmp_path))

    assert r.returncode == 4
    assert (tmp_path / "LICENSE").read_text() == "기존 내용\n"


def test_a_refused_run_writes_nothing_at_all(tmp_path):
    # 여러 파일을 요청했고 그중 하나만 이미 있으면, 나머지도 쓰지 않는다.
    (tmp_path / "SECURITY.md").write_text("기존\n")

    r = run("--file", "license", "--file", "security", "--license", "mit",
            "--holder", "S", "--out", str(tmp_path))

    assert r.returncode == 4
    assert not (tmp_path / "LICENSE").exists()


def test_mit_license_carries_the_holder_and_year(tmp_path):
    r = run("--file", "license", "--license", "mit", "--holder", "Seongjin",
            "--year", "2026", "--out", str(tmp_path))

    assert r.returncode == 0
    text = (tmp_path / "LICENSE").read_text()
    assert "Copyright (c) 2026 Seongjin" in text
    assert "[fullname]" not in text


def test_a_code_of_conduct_without_a_contact_warns_and_keeps_the_placeholder(tmp_path):
    # 신고 창구 없는 CoC는 지킬 수 없는 약속이다. 조용히 채우지 말고 남겨 둔다.
    r = run("--file", "code_of_conduct", "--out", str(tmp_path))

    assert r.returncode == 0
    assert "[INSERT CONTACT METHOD]" in (tmp_path / "CODE_OF_CONDUCT.md").read_text()
    assert "연락처" in r.stderr
