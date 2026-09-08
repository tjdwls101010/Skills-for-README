"""gh 조회. 실패한 항목은 None으로 남고 나머지 조회는 계속된다."""
import base64
import json

import pytest

from showcase import github
from showcase.github import GhError


def make_runner(responses):
    """args의 마지막 경로에 맞는 응답을 준다. 값이 GhError면 그 항목만 실패한다."""
    def runner(args):
        path = args[1]
        if path not in responses:
            raise GhError(f"unexpected call: {path}")
        value = responses[path]
        if isinstance(value, Exception):
            raise value
        return json.dumps(value)
    return runner


def test_security_file_in_dot_github_is_found(tmp_path):
    # 루트만 보고 부재를 단정하면 .github/SECURITY.md를 놓친다.
    (tmp_path / "README.md").write_text("# t\n")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "SECURITY.md").write_text("report to ...\n")

    facts = github.from_local_path(tmp_path)

    assert facts.security_paths == [".github/SECURITY.md"]
    assert facts.contributing_paths == []


def test_a_failing_endpoint_leaves_its_field_unknown_and_the_rest_intact():
    runner = make_runner({
        "repos/o/r": {"description": "d", "topics": ["a"], "homepage": "",
                      "license": {"spdx_id": "MIT"}},
        "repos/o/r/readme": {"path": "README.md",
                             "content": base64.b64encode(b"# t\n").decode()},
        "repos/o/r/community/profile": GhError("404"),
        "repos/o/r/releases": [{"tag_name": "v1"}],
    })

    facts = github.from_remote("o/r", runner=runner)

    assert facts.description == "d"
    assert facts.releases_count == 1
    assert facts.security_paths is None          # 없음이 아니라 모름
    assert any("community/profile" in e for e in facts.errors)


def test_noassertion_license_is_not_reported_as_a_detected_license():
    # jq 패턴. 파일은 있지만 GitHub이 식별하지 못한다.
    runner = make_runner({
        "repos/o/r": {"license": {"spdx_id": "NOASSERTION"}},
        "repos/o/r/readme": {"path": "README.md", "content": ""},
        "repos/o/r/community/profile": {"files": {"license": {"html_url": "u"}}},
        "repos/o/r/releases": [],
    })

    facts = github.from_remote("o/r", runner=runner)

    assert facts.license_key == ""
    assert facts.has_license_file is True


def test_an_unreachable_repo_yields_no_facts_but_records_why():
    runner = make_runner({"repos/o/r": GhError("gh: Not Found")})

    facts = github.from_remote("o/r", runner=runner)

    assert facts.has_license_file is None
    assert facts.readme_text is None
    assert facts.errors and "Not Found" in facts.errors[0]


def test_social_preview_is_read_from_graphql_not_guessed():
    # REST 응답에는 이 사실이 없다. 없다고 단정하면 "기본 이미지"와 "확인 못 함"이 섞인다.
    calls = []

    def runner(args):
        calls.append(args)
        if args[1] == "graphql":
            return json.dumps({"data": {"repository": {"usesCustomOpenGraphImage": True}}})
        raise GhError("unused")

    assert github.has_custom_social_preview("o/r", runner=runner) is True
    assert calls[0][:2] == ["api", "graphql"]


def test_social_preview_is_unknown_when_graphql_fails():
    def runner(args):
        raise GhError("HTTP 403")

    assert github.has_custom_social_preview("o/r", runner=runner) is None
