#!/usr/bin/env python3
"""LICENSE·CONTRIBUTING·CODE_OF_CONDUCT·SECURITY를 원문 그대로 만든다.

원문을 손으로 옮기면 조항이 바뀌고, 바뀐 라이선스는 라이선스가 아니다.
기존 파일은 덮어쓰지 않는다 — 이미 있는 약속을 지우는 것이기 때문이다."""
from __future__ import annotations

import argparse
import datetime
import subprocess
import sys
from pathlib import Path

TEMPLATES = Path(__file__).resolve().parent / "showcase" / "templates"

LICENSES = ("mit", "apache-2.0", "gpl-3.0", "bsd-3-clause")
OUTPUT_NAMES = {
    "license": "LICENSE",
    "contributing": "CONTRIBUTING.md",
    "code_of_conduct": "CODE_OF_CONDUCT.md",
    "security": "SECURITY.md",
}

EXIT_OK, EXIT_USAGE, EXIT_EXISTS = 0, 2, 4


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="scaffold_community.py",
        description=("커뮤니티 파일을 원문 그대로 만든다. 기존 파일이 있으면 "
                     "아무것도 쓰지 않고 종료한다."),
        epilog=("종료 코드: 0 생성, 2 인자 오류, 4 기존 파일 존재(--force 없음). "
                "자리표시자([CONTACT] 등)는 일부러 남긴다 — 지킬 수 없는 약속을 "
                "스크립트가 대신 채우지 않기 위한 것이다."),
    )
    p.add_argument("--file", action="append", dest="files", required=True,
                   choices=sorted(OUTPUT_NAMES), metavar="{license,contributing,code_of_conduct,security}",
                   help="만들 파일. 반복할 수 있다")
    p.add_argument("--license", choices=LICENSES,
                   help="--file license일 때 필수. 원문은 templates/에서 글자 그대로 온다")
    p.add_argument("--holder", help="LICENSE 저작권자. 기본값은 git config user.name")
    p.add_argument("--year", help="LICENSE 연도. 기본값은 올해")
    p.add_argument("--contact", help="CoC·SECURITY의 신고 연락처. 없으면 자리표시자를 남기고 경고한다")
    p.add_argument("--out", default=".", metavar="DIR", help="출력 디렉터리 (기본: 현재 디렉터리)")
    p.add_argument("--force", action="store_true", help="기존 파일 덮어쓰기를 허용한다")
    return p


def _git_user_name() -> str:
    try:
        r = subprocess.run(["git", "config", "user.name"], capture_output=True, text=True)
        return r.stdout.strip()
    except OSError:
        return ""


def render(kind: str, args) -> tuple[str, list[str]]:
    """(본문, 남은 자리표시자 경고)"""
    warnings = []
    if kind == "license":
        text = (TEMPLATES / f"LICENSE-{args.license}.txt").read_text(encoding="utf-8")
        holder = args.holder or _git_user_name()
        year = args.year or str(datetime.date.today().year)
        if not holder:
            warnings.append("저작권자를 정하지 못했다(--holder). [fullname]을 남긴다.")
        else:
            for token in ("[fullname]", "[name of copyright owner]", "<name of author>"):
                text = text.replace(token, holder)
        for token in ("[year]", "[yyyy]", "<year>"):
            text = text.replace(token, year)
        return text, warnings

    text = (TEMPLATES / OUTPUT_NAMES[kind]).read_text(encoding="utf-8")
    if args.contact:
        for token in ("[INSERT CONTACT METHOD]", "[CONTACT]"):
            text = text.replace(token, args.contact)
    elif kind in ("code_of_conduct", "security"):
        warnings.append(
            f"{OUTPUT_NAMES[kind]}: 신고 연락처(--contact)가 없어 자리표시자를 남겼다. "
            "받을 창구 없는 신고 안내는 지킬 수 없는 약속이다.")
    return text, warnings


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if "license" in args.files and not args.license:
        print("--file license에는 --license가 필요하다. 권리관계를 스크립트가 정하지 않는다.",
              file=sys.stderr)
        return EXIT_USAGE

    out = Path(args.out)
    targets = {k: out / OUTPUT_NAMES[k] for k in dict.fromkeys(args.files)}

    existing = [str(p) for p in targets.values() if p.exists()]
    if existing and not args.force:
        print("이미 있는 파일이 있어 아무것도 쓰지 않았다:\n  " + "\n  ".join(existing),
              file=sys.stderr)
        print("덮어쓰려면 --force. 지우기 전에 기존 내용을 먼저 읽는다.", file=sys.stderr)
        return EXIT_EXISTS

    rendered = {}
    for kind in targets:
        rendered[kind], warns = render(kind, args)
        for w in warns:
            print(f"경고: {w}", file=sys.stderr)

    out.mkdir(parents=True, exist_ok=True)
    for kind, path in targets.items():
        path.write_text(rendered[kind], encoding="utf-8")
        print(f"만듦: {path}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
