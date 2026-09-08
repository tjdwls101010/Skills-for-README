"""README 텍스트에서 구조 지표를 뽑는다. 판정하지 않는다 — 합격점은 없다."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# 설치 헤딩의 언어별 표기. 수집 단계 스크립트는 영어만 봐서 한국어 "## 설치"를
# 놓쳤다. 코퍼스에 실제로 나타난 표기만 넣는다 — 사전을 넓히면 "Getting the
# source"처럼 설치가 아닌 헤딩까지 걸린다.
INSTALL_WORDS = (
    "install", "installation", "installing", "setup", "set up", "set-up",
    "get started", "getting started", "quick start", "quickstart",
    "설치", "시작하기", "빠른 시작",
    "インストール", "导入", "安装", "使用方法",
    "instalación", "installation", "instalação", "установка",
)

# 코드 블록으로 세지 않는 정보 펜스. Mermaid는 다이어그램이지 실행 가능한
# 명령이 아니어서 "첫 코드 줄"을 앞당겨 오판을 만든다(코덱스 발견 버그 b).
NON_CODE_LANGS = {"mermaid", "math", "latex", "diff", "text", "txt", "plaintext", "none"}


@dataclass
class Heading:
    line: int
    level: int
    text: str


@dataclass
class CodeBlock:
    line: int          # 펜스 여는 줄 (1부터)
    lang: str
    body: str


@dataclass
class Image:
    line: int
    alt: str
    url: str
    kind: str          # "badge" | "logo" | "result"


@dataclass
class ReadmeMetrics:
    lines: int = 0
    words: int = 0
    headings: list[Heading] = field(default_factory=list)
    code_blocks: list[CodeBlock] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)
    install_heading_line: int | None = None
    first_code_line: int | None = None
    first_result_image_line: int | None = None
    badges: int = 0


def _norm(s: str) -> str:
    """구두점·이모지만 공백으로. 문자는 스크립트를 가리지 않고 남긴다 —
    한글·가나·한자·키릴을 지우면 그 언어의 헤딩이 빈 문자열이 되어 모든 헤딩과 일치한다."""
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", s.lower())).strip()


def parse_headings(text: str) -> list[Heading]:
    out = []
    for i, raw in enumerate(_code_masked_lines(text), start=1):
        m = re.match(r"^(#{1,6})\s+(.*?)\s*#*\s*$", raw)
        if m:
            out.append(Heading(i, len(m.group(1)), m.group(2).strip()))
    return out


def _code_masked_lines(text: str) -> list[str]:
    """펜스 안의 줄을 빈 줄로 바꾼 사본. 코드 안의 `# 주석`이 헤딩으로 세지는 것을 막는다."""
    out, fence = [], None
    for raw in text.splitlines():
        m = re.match(r"^\s*(`{3,}|~{3,})", raw)
        if m and fence is None:
            fence = m.group(1)[0] * 3
            out.append("")
            continue
        if fence and m and m.group(1)[0] * 3 == fence:
            fence = None
            out.append("")
            continue
        out.append("" if fence else raw)
    return out


_INSTALL_NORM = tuple(sorted({_norm(w) for w in INSTALL_WORDS}))


def find_install_heading(headings: list[Heading]) -> int | None:
    for h in headings:
        t = _norm(h.text)
        if any(w in t for w in _INSTALL_NORM):
            return h.line
    return None


# 배지를 내주는 호스트. 이 목록에 없는 이미지를 배지로 오인하면 결과 증거가
# 없는 README를 "증거 있음"으로 읽게 되므로, 호스트 판별을 alt 텍스트보다 앞에 둔다.
BADGE_HOSTS = (
    "img.shields.io", "badge.fury.io", "travis-ci", "circleci.com",
    "codecov.io", "coveralls.io", "badgen.net", "github.com/.*/badge",
    "githubusercontent.com/.*badge", "api.codeclimate.com", "snyk.io/test",
    "opencollective.com", "isitmaintained.com", "forthebadge.com",
    "img.buymeacoffee.com", "static.pepy.tech", "pepy.tech/badge",
    "actions/workflows/.*badge.svg", "/actions/workflows/",
)
LOGO_WORDS = ("logo", "banner", "wordmark", "icon", "header", "hero")


def classify_image(alt: str, url: str) -> str:
    u = url.lower()
    if any(re.search(h, u) for h in BADGE_HOSTS) or u.endswith("badge.svg"):
        return "badge"
    a = alt.lower()
    if any(w in a for w in LOGO_WORDS) or any(w in u for w in LOGO_WORDS):
        return "logo"
    return "result"


def parse_images(text: str) -> list[Image]:
    """마크다운 이미지와 <img> 태그. 링크로 감싼 배지도 이미지 자체를 본다."""
    out = []
    for i, raw in enumerate(_code_masked_lines(text), start=1):
        for m in re.finditer(r"!\[([^\]]*)\]\(\s*<?([^\s)>]+)", raw):
            out.append(Image(i, m.group(1), m.group(2), classify_image(m.group(1), m.group(2))))
        for m in re.finditer(r"<img\b[^>]*>", raw, re.I):
            tag = m.group(0)
            src = re.search(r'src\s*=\s*["\']([^"\']+)', tag, re.I)
            alt = re.search(r'alt\s*=\s*["\']([^"\']*)', tag, re.I)
            if src:
                a = alt.group(1) if alt else ""
                out.append(Image(i, a, src.group(1), classify_image(a, src.group(1))))
    return out


def parse_code_blocks(text: str) -> list[CodeBlock]:
    """실행 가능한 것으로 읽히는 펜스만. 다이어그램·수식 펜스는 제외한다."""
    out, fence, lang, start, body = [], None, "", 0, []
    for i, raw in enumerate(text.splitlines(), start=1):
        m = re.match(r"^\s*(`{3,}|~{3,})\s*([A-Za-z0-9_+-]*)", raw)
        if m and fence is None:
            fence, lang, start, body = m.group(1)[0] * 3, m.group(2).lower(), i, []
            continue
        if fence is not None and m and m.group(1)[0] * 3 == fence and not m.group(2):
            if lang not in NON_CODE_LANGS:
                out.append(CodeBlock(start, lang, "\n".join(body)))
            fence = None
            continue
        if fence is not None:
            body.append(raw)
    return out


def analyze(text: str) -> ReadmeMetrics:
    m = ReadmeMetrics()
    m.lines = len(text.splitlines())
    m.words = len(text.split())
    m.headings = parse_headings(text)
    m.install_heading_line = find_install_heading(m.headings)
    m.code_blocks = parse_code_blocks(text)
    m.first_code_line = m.code_blocks[0].line if m.code_blocks else None
    m.images = parse_images(text)
    m.badges = sum(1 for im in m.images if im.kind == "badge")
    results = [im.line for im in m.images if im.kind == "result"]
    m.first_result_image_line = results[0] if results else None
    return m
