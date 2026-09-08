"""`gh`로 레포 사실을 모은다. 모르는 것은 None으로 남긴다 — 없는 것과 다르다.

`None`은 "조회하지 않았거나 실패했다", `False`/`[]`는 "조회했고 없다"를 뜻한다.
이 구분이 사라지면 `--offline` 실행이 "라이선스 없음"을 단정하게 된다."""
from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

# SECURITY·CONTRIBUTING·CoC가 놓일 수 있는 자리. 루트만 보고 부재를 단정할 수 없다.
COMMUNITY_DIRS = ("", ".github/", "docs/")
COMMUNITY_FILES = {
    "security": ("SECURITY.md", "SECURITY.rst", "SECURITY.txt", "SECURITY"),
    "contributing": ("CONTRIBUTING.md", "CONTRIBUTING.rst", "CONTRIBUTING.txt", "CONTRIBUTING"),
    "code_of_conduct": ("CODE_OF_CONDUCT.md", "CODE_OF_CONDUCT.rst", "CODE_OF_CONDUCT.txt", "CODE_OF_CONDUCT"),
}
LICENSE_FILES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "LICENCE", "LICENCE.md", "COPYING", "COPYING.md")


@dataclass
class RepoFacts:
    target: str = ""
    description: str | None = None
    topics: list[str] | None = None
    homepage: str | None = None
    license_key: str | None = None
    has_license_file: bool | None = None
    security_paths: list[str] | None = None
    contributing_paths: list[str] | None = None
    code_of_conduct_paths: list[str] | None = None
    releases_count: int | None = None
    readme_path: str | None = None
    readme_text: str | None = None
    errors: list[str] = field(default_factory=list)


class GhError(RuntimeError):
    pass


def run_gh(args: list[str]) -> str:
    """`gh`를 한 번 부른다. 테스트는 이 함수를 대신 넣는다."""
    if not shutil.which("gh"):
        raise GhError("gh CLI를 찾을 수 없다")
    p = subprocess.run(["gh", *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise GhError((p.stderr or p.stdout).strip()[:400])
    return p.stdout


def from_local_path(path: str | Path, readme_path: str | None = None) -> RepoFacts:
    """파일시스템만 읽는다. 원격 메타데이터(description·topics·releases)는 None으로 남는다."""
    root = Path(path)
    facts = RepoFacts(target=str(root))
    readme = Path(readme_path) if readme_path else _find_readme(root)
    if readme and readme.is_file():
        facts.readme_path = str(readme)
        facts.readme_text = readme.read_text(encoding="utf-8", errors="replace")
    else:
        facts.errors.append(f"README를 찾지 못했다: {root}")
    facts.has_license_file = any((root / n).is_file() for n in LICENSE_FILES)
    for key, names in COMMUNITY_FILES.items():
        found = [f"{d}{n}" for d in COMMUNITY_DIRS for n in names if (root / d / n).is_file()]
        setattr(facts, f"{key}_paths", found)
    return facts


def _find_readme(root: Path) -> Path | None:
    for name in ("README.md", "README.rst", "README.txt", "README", "readme.md"):
        if (root / name).is_file():
            return root / name
    return None


def from_remote(target: str, runner=run_gh) -> RepoFacts:
    """owner/repo를 gh로 조회한다. 항목마다 따로 실패할 수 있어 따로 감싼다."""
    facts = RepoFacts(target=target)
    try:
        repo = json.loads(runner(["api", f"repos/{target}"]))
    except (GhError, ValueError) as e:
        facts.errors.append(f"repos/{target}: {e}")
        return facts
    facts.description = repo.get("description") or ""
    facts.topics = repo.get("topics") or []
    facts.homepage = repo.get("homepage") or ""
    lic = repo.get("license") or {}
    key = (lic.get("spdx_id") or lic.get("key") or "").lower()
    facts.license_key = "" if key in ("", "noassertion") else key
    facts.has_license_file = bool(facts.license_key)

    try:
        readme = json.loads(runner(["api", f"repos/{target}/readme"]))
        import base64
        facts.readme_path = readme.get("path")
        facts.readme_text = base64.b64decode(readme.get("content", "")).decode("utf-8", "replace")
    except (GhError, ValueError) as e:
        facts.errors.append(f"repos/{target}/readme: {e}")

    try:
        profile = json.loads(runner(["api", f"repos/{target}/community/profile"]))
        files = profile.get("files") or {}
        facts.has_license_file = facts.has_license_file or bool(files.get("license"))
        for key_name, api_key in (("security", "security"),
                                  ("contributing", "contributing"),
                                  ("code_of_conduct", "code_of_conduct_file")):
            entry = files.get(api_key)
            setattr(facts, f"{key_name}_paths", [entry["html_url"]] if entry else [])
    except (GhError, ValueError) as e:
        facts.errors.append(f"repos/{target}/community/profile: {e}")

    try:
        rels = json.loads(runner(["api", f"repos/{target}/releases", "--paginate"]))
        facts.releases_count = len(rels)
    except (GhError, ValueError) as e:
        facts.errors.append(f"repos/{target}/releases: {e}")
    return facts
