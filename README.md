# Skills for README

**A Claude Code skill that fixes what a GitHub visitor sees first — from evidence, not taste.**

Point it at a repo and it audits the README and GitHub metadata, interviews you about the things only you know, and rewrites the first screen so a visitor can answer three questions: *what is this, is it for me, how do I try it.*

It is not a template filler. `readme-ai` and `readme-md-generator` produce a README from your repo's contents; this one starts by telling you which of your claims it could not find evidence for, and refuses to write the ones you cannot back.

```
$ python3 scripts/audit_repo.py tjdwls101010/Ultra-Search

## 채택을 막는 결손

[present      ] license_missing
                사용·수정·재배포 조건을 확인할 수 없으면 소개가 좋아도 채택을 보류한다.
[undetermined ] prereq_unstated
                전제조건이 첫 명령(19번째 줄)보다 뒤에 있다. 도입을 막는 조건인지는 내용을 읽고 판정한다.

## 설득력 개선

[absent       ] result_evidence
[absent       ] description
                비어 있다. 검색 결과와 프로필 목록에서 레포가 자기를 설명할 기회가 사라진다.
```

Every judgment carries the line it came from. **There is no score** — structural metrics only get compared before and after.

## Requirements

- **Claude Code.** This is a skill, not a standalone tool.
- **`gh` CLI, logged in.** Used read-only for repo metadata; nothing is written to a remote without your approval.
- **Python 3.9+**, standard library only. No packages to install.
- Optional: [`vhs`](https://github.com/charmbracelet/vhs) if you want it to record a terminal demo.

macOS only, so far — nothing in it should be platform-specific, but Linux and Windows are untested.

## Install

```bash
git clone https://github.com/tjdwls101010/Skills-for-README.git
ln -s "$PWD/Skills-for-README/.claude/skills/repo-showcase" ~/.claude/skills/repo-showcase
```

Then in any Claude Code session:

> 이 레포 README 좀 제대로 써줘

The skill loads on its own — you should see `repo-showcase` in Claude's response. It will run the audit, ask you about eleven things it cannot determine from your code, and write from your answers.

Verified: on six requests phrased that way it loaded every time, and on four adjacent requests (docstrings, a docs site, a blog post, an API reference) it stayed out of the way.

## What it touches

| It writes | It proposes, you run |
|---|---|
| `README.md`, `README.ko.md` | `gh repo edit --description --add-topic --homepage` |
| `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md` (only if missing) | Releases, social preview, profile pins |
| `LAUNCH-KIT.md` — pitch, demo path, Show HN title candidates | Any push, PR, or post |

**It never writes to a remote on its own, never overwrites an existing community file, and never contacts your stargazers.** The last one is deliberate: that would breach platform terms and reads as spam.

## Security note

This skill runs with your agent's permissions. It reads your repo, calls `gh api` for public metadata, and writes files in your working directory. It does not send your code anywhere. Review `.claude/skills/repo-showcase/scripts/` before installing — that is the same advice this skill will give your visitors about your project.

## Where the advice comes from

Not from README best-practice lists. From 97 READMEs measured directly: 73 current ones across five tiers, plus the 3-month and 9-month snapshots of 12 tools that later became well known.

Two findings do most of the work:

- **The model for a 0-star repo is not today's `bat` but `bat` at three months** — 203 lines, install at line 20, a result on the first screen. Today's version is 514 lines with install at line 74, and that layout is something recognition buys you.
- **What separates low-traction repos is not length or install position** (those don't separate them at all) **but whether the first screen shows a result** — 7/20 versus 10/12 — and whether the one-line definition connects to something the visitor already knows: 0/20 versus 4/12.

The numbers, the reproduction command, and the limits are in [`research/metrics-summary.md`](research/metrics-summary.md). Design decisions and what was deliberately left out are in [`research/decisions.md`](research/decisions.md).

**What this cannot tell you:** whether any of it grows a project. There is no conversion data, and longitudinal research reports the reverse direction — popularity brings documentation work. What the skill claims is narrower: that a visitor can decide from your documents.

## Development

```bash
python3 -m pytest          # 53 tests
python3 research/aggregate_corpus.py   # regenerate the corpus table (needs .tmp/, see the manifest)
```

The corpus itself is not committed. [`research/corpus-manifest.json`](research/corpus-manifest.json) has every repo, tier, and README blob SHA, so it can be refetched exactly.

## License

MIT. See [LICENSE](LICENSE).

---

한국어 README가 필요하면 이슈로 알려 주세요.
