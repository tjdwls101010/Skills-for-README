"""CLI 계약: 종료 코드와 --json 스키마. 스킬이 의존하는 것은 이 표면이다."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

from conftest import FIXTURES

AUDIT = (Path(__file__).resolve().parents[1] / ".claude" / "skills" /
         "repo-showcase" / "scripts" / "audit_repo.py")
SIMILAR = AUDIT.parent / "similar_repos.py"


def run(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True)


def make_repo(tmp_path, readme_name, license_text=None):
    shutil.copy(FIXTURES / "readmes" / readme_name, tmp_path / "README.md")
    if license_text:
        (tmp_path / "LICENSE").write_text(license_text)
    return tmp_path


def test_audit_exits_zero_even_when_it_finds_blockers(tmp_path):
    # 결손이 있다고 실패로 끝나면 호출부가 '실행 실패'와 '결손 있음'을 구별하지 못한다.
    repo = make_repo(tmp_path, "synthetic_low_traction.md")

    r = run(AUDIT, str(repo), "--offline", "--json")

    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert any(b["state"] == "present" for b in data["blockers"])


def test_audit_json_carries_every_declared_key(tmp_path):
    repo = make_repo(tmp_path, "synthetic_early_classic.md", "MIT License\n")

    data = json.loads(run(AUDIT, str(repo), "--offline", "--json").stdout)

    assert set(data) >= {"target", "fetched", "blockers", "persuasion", "metrics", "compare"}
    assert {b["id"] for b in data["blockers"]} == {
        "license_missing", "license_mismatch", "prereq_unstated",
        "start_path_unreproducible", "status_contradiction"}
    assert {p["id"] for p in data["persuasion"]} == {
        "one_liner", "result_evidence", "start_path", "description",
        "topics", "homepage", "releases", "social_preview"}
    assert set(data["metrics"]) == {
        "lines", "words", "badges", "first_result_image_line", "first_code_line",
        "install_heading_line", "one_liner_line", "one_liner_len", "evidence_types"}


def test_offline_never_claims_remote_metadata_is_absent(tmp_path):
    repo = make_repo(tmp_path, "synthetic_early_classic.md")

    data = json.loads(run(AUDIT, str(repo), "--offline", "--json").stdout)
    remote = {p["id"]: p["state"] for p in data["persuasion"]}

    assert remote["description"] == "lookup_failed"
    assert remote["topics"] == "lookup_failed"
    assert remote["releases"] == "lookup_failed"


def test_offline_against_a_remote_target_is_a_usage_error():
    r = run(AUDIT, "owner/repo", "--offline")

    assert r.returncode == 2
    assert "--offline" in r.stderr


def test_a_nonexistent_target_is_unreachable():
    # 종료 코드 3은 "대상에 닿지 못했다"이지 "README가 아직 없다"가 아니다.
    r = run(AUDIT, "no-such-owner-xyz/no-such-repo-xyz")

    assert r.returncode == 3


def test_similar_repos_rejects_a_zero_limit():
    r = run(SIMILAR, "--query", "x", "--limit", "0")

    assert r.returncode == 2


def test_compare_against_an_unreachable_repo_does_not_look_like_an_empty_repo(tmp_path):
    # gh 조회가 실패했는데 topics가 [] 로 나오면 "topic이 없는 레포"와 구별되지 않고,
    # missing_topics가 비어 있으니 제안할 것이 없다는 결론까지 나온다.
    repo = make_repo(tmp_path, "synthetic_early_classic.md")

    data = json.loads(run(AUDIT, str(repo), "--compare", "no-such-owner/no-such-repo-xyz",
                          "--json").stdout)

    assert data["compare"]["state"] == "lookup_failed"
    assert data["compare"]["missing_topics"] is None
    assert data["errors"]


def test_a_repo_with_no_readme_yet_is_still_audited(tmp_path):
    # README를 처음 쓰는 레포가 이 스킬의 주 대상이다. 종료 코드 3으로 끝나면
    # 아무 판정도 못 받는다. README에서 오는 항목만 absent로 남는다.
    (tmp_path / "LICENSE").write_text("MIT License\n")

    r = run(AUDIT, str(tmp_path), "--offline", "--json")

    assert r.returncode == 0
    data = json.loads(r.stdout)
    assert data["readme_path"] is None
    assert {b["id"]: b["state"] for b in data["blockers"]}["license_missing"] == "absent"
    assert {p["id"]: p["state"] for p in data["persuasion"]}["one_liner"] == "absent"
