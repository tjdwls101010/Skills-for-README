import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "repo-showcase" / "scripts"
FIXTURES = Path(__file__).resolve().parent / "fixtures"

sys.path.insert(0, str(SCRIPTS))


def fixture_text(name):
    return (FIXTURES / "readmes" / name).read_text(encoding="utf-8")
