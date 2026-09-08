#!/usr/bin/env python3
"""가장 가까운 대안 레포 후보를 찾는다. 사람 정보는 조회하지 않는다."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from showcase import github, similar  # noqa: E402

EXIT_OK, EXIT_USAGE, EXIT_UNREACHABLE, EXIT_EMPTY = 0, 2, 3, 5


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="similar_repos.py",
        description=("한 줄 정의와 topics로 유사 프로젝트 후보를 찾는다. 고른 레포는 "
                     "topics 어휘 정렬, 비교표, 한 줄 정의의 앵커, 'Similar projects' "
                     "절 추가 PR 후보에 쓴다."),
        epilog=("정렬: 스타 내림차순. 단 1년 이상 갱신되지 않은 레포는 뒤로 보낸다 — "
                "죽은 프로젝트를 대안으로 골라 비교표에 쓰면 낡은 정보가 굳는다. "
                "종료 코드: 0, 2 인자 오류, 3 gh 접근 실패, 5 결과 없음. "
                "스타게이저·기여자 등 사람 정보는 조회하지 않는다."),
    )
    p.add_argument("--query", required=True,
                   help="검색어. 한 줄 정의의 핵심 명사·동사를 넣으면 불용어는 알아서 빠진다")
    p.add_argument("--topic", action="append", dest="topics", metavar="T",
                   help="GitHub topic 필터. 반복할 수 있다")
    p.add_argument("--language", metavar="L", help="주 언어 필터")
    p.add_argument("--limit", type=int, default=10, help="후보 수 (기본 10)")
    p.add_argument("--exclude", action="append", dest="excludes", metavar="OWNER/REPO",
                   help="결과에서 뺄 레포. 보통 대상 자신")
    p.add_argument("--json", action="store_true", help="JSON 출력 (기본: 사람용 표)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.limit < 1:
        print("--limit은 1 이상이어야 한다", file=sys.stderr)
        return EXIT_USAGE

    query = similar.build_query(args.query, args.topics, args.language)
    try:
        found = similar.search(query, args.limit + len(args.excludes or []))
    except github.GhError as e:
        print(f"gh 검색 실패: {e}", file=sys.stderr)
        return EXIT_UNREACHABLE

    excluded = {e.lower() for e in (args.excludes or [])}
    found = [c for c in found if c["repo"].lower() not in excluded][:args.limit]
    if not found:
        print(f"결과 없음. 검색어: {query}", file=sys.stderr)
        return EXIT_EMPTY

    ranked = similar.rank(found)
    if args.json:
        print(json.dumps({"query": query, "candidates": ranked}, ensure_ascii=False, indent=2))
        return EXIT_OK

    print(f"검색어: {query}\n")
    for c in ranked:
        print(f"{c['repo']}  ★{c['stars']}  {c['license'] or 'no-license'}  갱신 {c['pushed_at']}")
        if c["description"]:
            print(f"    {c['description'][:120]}")
        if c["topics"]:
            print(f"    topics: {', '.join(c['topics'][:10])}")
    print("\n이 중 1~3개를 고른 뒤 audit_repo.py --compare 로 어휘를 대조한다.")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
