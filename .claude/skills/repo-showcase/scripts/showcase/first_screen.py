"""첫 화면의 세 답 — 한 줄 정의, 결과 증거, 시작 경로 — 을 텍스트에서 찾는다.

찾지 못하면 없다고 말한다. 좋은지 나쁜지는 말하지 않는다."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import readme_metrics


@dataclass
class OneLiner:
    line: int
    text: str
    length: int
    alternatives: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    kind: str          # "gif" | "screenshot" | "output_block" | "online_demo"
    line: int
    text: str


@dataclass
class StartPath:
    """방문자가 첫 성공까지 밟는 경로의 세 요소가 어디에 있는지."""
    prereq_lines: list[int] = field(default_factory=list)
    command_lines: list[int] = field(default_factory=list)
    expected_result_lines: list[int] = field(default_factory=list)


@dataclass
class FirstScreen:
    one_liner: OneLiner | None = None
    evidence: list[Evidence] = field(default_factory=list)
    start_path: StartPath = field(default_factory=StartPath)


# "무엇의 대안인가"를 관찰 가능하게 만드는 표현. 방문자가 아는 도구에 자신을
# 연결하는 문장은 코퍼스의 초기 고전에서 거의 항상 이 중 하나를 쓴다.
COMPARISON_PATTERNS = (
    r"alternative to\s+(.+?)(?:[.,;]|$)",
    r"replacement for\s+(.+?)(?:[.,;]|$)",
    r"drop-in\s+(.+?)\s+replacement",
    r"(?:a|an)\s+(.+?)\s+clone",
    r"clone of\s+(.+?)(?:[.,;]|$)",
    r"instead of\s+(.+?)(?:[.,;]|$)",
    r"faster\s+(?:way|version)\s+to\s+(.+?)(?:[.,;]|$)",
    r"like\s+(.+?),?\s+but\b",
    r"successor to\s+(.+?)(?:[.,;]|$)",
    r"(.+?)\s*대신\b",
    r"(.+?)\s*의 대안\b",
)

_PROSE_SKIP = re.compile(r"^\s*(?:[#>\-*+]|\d+\.|\||!\[|<img|<p|<div|<a\b|\[!\[|`{3}|~{3}|<!--)")


def _paragraphs(text: str) -> list[tuple[int, str]]:
    """(시작 줄, 한 줄로 접은 본문) 목록. 코드 펜스 안은 비운다."""
    out, buf, start = [], [], 0
    for i, raw in enumerate(readme_metrics._code_masked_lines(text) + [""], start=1):
        if raw.strip():
            if not buf:
                start = i
            buf.append(raw.strip())
        elif buf:
            out.append((start, " ".join(buf)))
            buf = []
    return out


def find_one_liner(text: str) -> OneLiner | None:
    """제목 다음의 첫 산문 문단. 배지 줄·이미지·목록·인용은 건너뛴다."""
    for line, body in _paragraphs(text):
        if _PROSE_SKIP.match(body):
            continue
        stripped = re.sub(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)|!\[[^\]]*\]\([^)]*\)", "", body).strip()
        if not stripped:
            continue
        return OneLiner(line, stripped, len(stripped), find_alternatives(stripped))
    return None


def find_alternatives(sentence: str) -> list[str]:
    out = []
    for pat in COMPARISON_PATTERNS:
        for m in re.finditer(pat, sentence, re.I):
            name = m.group(1).strip().strip("`\"'*_ ")
            # 절 하나보다 길면 도구 이름이 아니라 설명이다.
            if name and len(name.split()) <= 4 and name.lower() not in out:
                out.append(name.lower())
    return out


# 실행해 보지 않고도 결과를 보여주는 링크. "docs"·"website"는 결과가 아니라
# 더 읽을 거리이므로 넣지 않는다.
DEMO_LINK_WORDS = (
    "try it", "try online", "live demo", "playground", "online demo",
    "demo", "sandbox", "repl", "체험", "데모",
)
# 명령과 출력을 함께 보여주는 블록의 언어 표기.
SESSION_LANGS = {"console", "shell-session", "shellsession", "session", "sh-session"}


def _is_output_block(block: readme_metrics.CodeBlock) -> bool:
    """명령 다음에 그 결과가 오는 블록. 명령만 나열된 설치 블록과 구별한다."""
    if block.lang in SESSION_LANGS:
        return True
    lines = [l for l in block.body.splitlines() if l.strip()]
    for i, l in enumerate(lines):
        if re.match(r"^\s*[$>%#]\s+\S", l):
            rest = lines[i + 1:]
            if any(not re.match(r"^\s*[$>%#]\s", r) for r in rest):
                return True
    return False


def find_evidence(text: str) -> list[Evidence]:
    out = []
    for im in readme_metrics.parse_images(text):
        if im.kind != "result":
            continue
        kind = "gif" if im.url.lower().split("?")[0].endswith((".gif", ".webp", ".mp4", ".webm")) else "screenshot"
        out.append(Evidence(kind, im.line, im.alt or im.url))
    for b in readme_metrics.parse_code_blocks(text):
        if _is_output_block(b):
            out.append(Evidence("output_block", b.line, b.body.splitlines()[0] if b.body else ""))
    for i, raw in enumerate(readme_metrics._code_masked_lines(text), start=1):
        for m in re.finditer(r"\[([^\]]+)\]\((https?://[^)\s]+)", raw):
            label = m.group(1).lower()
            if any(w in label for w in DEMO_LINK_WORDS):
                out.append(Evidence("online_demo", i, m.group(1)))
    return sorted(out, key=lambda e: e.line)


# 전제조건을 말하는 표현. 문장 안 어디에나 올 수 있어 헤딩만 봐서는 놓친다.
PREREQ_PATTERNS = (
    r"\brequires?\b", r"\brequirements?\b", r"\bprerequisites?\b",
    r"\byou(?:'ll| will)? need\b", r"\bmust have\b", r"\bdepends on\b",
    r"\bassumes? (?:you|that)\b", r"\bonly works (?:on|with)\b",
    r"전제", r"필요합니다", r"있어야", r"필요하다",
)
# 실행하면 무엇이 나오는지 예고하는 표현. 출력 블록이 없어도 이건 답이 된다.
EXPECTED_RESULT_PATTERNS = (
    r"you (?:should|will) see", r"outputs?\b", r"prints?\b",
    r"결과(?:는|가)", r"출력(?:된다|됩니다|한다)",
)


def _matches(text: str, patterns) -> list[int]:
    out = []
    for i, raw in enumerate(readme_metrics._code_masked_lines(text), start=1):
        if any(re.search(p, raw, re.I) for p in patterns):
            out.append(i)
    return out


def find_start_path(text: str) -> StartPath:
    blocks = readme_metrics.parse_code_blocks(text)
    commands = [b.line for b in blocks if _has_command(b)]
    expected = sorted({b.line for b in blocks if _is_output_block(b)}
                      | set(_matches(text, EXPECTED_RESULT_PATTERNS)))
    return StartPath(_matches(text, PREREQ_PATTERNS), commands, expected)


def _has_command(block: readme_metrics.CodeBlock) -> bool:
    """실행할 명령이 들어 있는 블록. 설정 파일 예제(yaml·json·toml)는 아니다."""
    if block.lang in {"yaml", "yml", "json", "toml", "ini", "xml", "html", "css"}:
        return False
    return bool(block.body.strip())


def analyze(text: str) -> FirstScreen:
    return FirstScreen(
        one_liner=find_one_liner(text),
        evidence=find_evidence(text),
        start_path=find_start_path(text),
    )
