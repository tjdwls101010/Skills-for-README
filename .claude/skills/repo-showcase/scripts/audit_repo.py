#!/usr/bin/env python3
"""레포의 첫인상을 근거와 함께 판정한다. 점수는 내지 않는다."""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from showcase import github, report  # noqa: E402

EXIT_OK, EXIT_USAGE, EXIT_UNREACHABLE = 0, 2, 3


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="audit_repo.py",
        description=(
            "README·GitHub 메타데이터를 읽고 '채택을 막는 결손'과 '설득력 개선'을 "
            "근거 줄 번호와 함께 낸다. 합격/불합격 점수는 내지 않는다 — 구조 지표는 "
            "개선 전후 비교에만 쓴다."
        ),
        epilog=(
            "상태값 present는 묶음마다 가리키는 것이 다르다 — blockers에서는 "
            "'그 결손이 있다', persuasion에서는 '그 재료가 있다'. absent는 "
            "'조회했고 없다', lookup_failed는 '조회하지 못해 모른다', "
            "undetermined는 '자료는 있으나 읽어야 판정 가능'. "
            "README가 아직 없는 레포도 판정한다(README에서 오는 항목만 absent). "
            "종료 코드: 0 실행 성공(결손 유무와 무관), 2 인자 오류, "
            "3 대상 접근 실패(경로 없음·gh 조회 실패)."
        ),
    )
    p.add_argument("target",
                   help="owner/repo (gh로 조회) 또는 로컬 경로 (파일시스템에서 읽음)")
    p.add_argument("--compare", metavar="OWNER/REPO",
                   help="유사 프로젝트의 description·topics만 조회해 어휘 대조에 쓴다. "
                        "기능 비교나 PR 적합성 판단은 하지 않는다 — 그건 원문을 읽어야 한다")
    p.add_argument("--json", action="store_true",
                   help="사람용 보고 대신 JSON")
    p.add_argument("--offline", action="store_true",
                   help="gh를 부르지 않고 로컬 파일만 읽는다. 원격 항목은 lookup_failed로 남는다")
    p.add_argument("--readme", metavar="PATH",
                   help="README 파일을 직접 지정한다 (개선 전후 비교용)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    is_path = Path(args.target).exists()

    if args.offline and not is_path:
        print(f"--offline은 로컬 경로에만 쓸 수 있다: {args.target}", file=sys.stderr)
        return EXIT_USAGE
    if not is_path and "/" not in args.target:
        print(f"owner/repo 형식이거나 존재하는 경로여야 한다: {args.target}", file=sys.stderr)
        return EXIT_USAGE

    if is_path:
        facts = github.from_local_path(args.target, args.readme)
    else:
        facts = github.from_remote(args.target)
        if args.readme:
            facts.readme_path = args.readme
            facts.readme_text = Path(args.readme).read_text(encoding="utf-8", errors="replace")
        if facts.readme_text is None and facts.description is None:
            print("\n".join(facts.errors), file=sys.stderr)
            return EXIT_UNREACHABLE

    # README가 아직 없는 레포가 이 도구의 주 대상이다. 없다고 종료하면 처음
    # 쓰는 사람이 아무 판정도 받지 못한다. README에서 오는 항목만 absent가 된다.
    if facts.readme_text is None and not is_path and facts.description is None:
        print("\n".join(facts.errors) or "대상에 접근하지 못했다", file=sys.stderr)
        return EXIT_UNREACHABLE

    compare = None
    if args.compare and not args.offline:
        other = github.from_remote(args.compare)
        if other.topics is None:
            # 조회 실패를 빈 topics로 흘리면 "topic 없는 레포"로 읽히고,
            # missing_topics가 비어 제안할 것이 없다는 결론까지 나온다.
            compare = {"repo": args.compare, "state": "lookup_failed",
                       "description": None, "topics": None,
                       "shared_topics": None, "missing_topics": None}
            facts.errors.extend(other.errors)
        else:
            mine, theirs = set(facts.topics or []), set(other.topics)
            compare = {"repo": args.compare, "state": "present",
                       "description": other.description,
                       "topics": sorted(theirs), "shared_topics": sorted(mine & theirs),
                       "missing_topics": sorted(theirs - mine)}

    fetched = datetime.date.today().isoformat()
    data = report.build(facts, fetched, compare)
    print(json.dumps(data, ensure_ascii=False, indent=2) if args.json
          else report.render_text(data))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
