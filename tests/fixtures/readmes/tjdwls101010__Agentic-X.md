# agentic-x

![agentic-x](https://raw.githubusercontent.com/tjdwls101010/tjdwls101010/refs/heads/main/Images/scraper%20for%20x.png)

Read-only scraping of logged-in **X/Twitter** data via a **harvest-then-replay hybrid**: a stealth browser (or a cookie import) logs you in once and harvests the session, then every read afterward is a plain `httpx` GraphQL request — no browser in the loop.

Reads your **home feed**, **bookmarks** and **likes**; any profile's **posts, replies, media, highlights or articles**, and the **profile itself**; a tweet's **thread**; a **List**; **search** over posts or accounts; and the **social graph** (following / followers / retweeters). Each command is a single-target primitive; chaining them into multi-hop exploration is a caller's job, not the CLI's.

> **Read [DISCLAIMER.md](DISCLAIMER.md) before using this.** Using this tool violates X's Terms of Service, publishing it exposes its maintainer, and scraping other people's tweets can make *you* a data controller over their personal data under GDPR. Use a dedicated/throwaway account, not your primary one.

## Installation

Base install — cookie-import login only, **no browser dependency**:

```bash
pip install agentic-twitter
```

The `[browser]` extra — adds a stealth browser for `agentic-x login`:

```bash
pip install "agentic-twitter[browser]"
```

If you only ever import cookies from a session you already have (e.g. exported from your own logged-in browser), the base install is all you need.

## Quick Start

```bash
# 1. One-time interactive login — opens a real browser window, you log in by hand.
agentic-x login

# 2. Fetch a profile's tweets.
agentic-x fetch nasa --limit 50
```

## CLI overview

| Command | Purpose |
|---|---|
| `agentic-x login` | One-time login: headed stealth browser by default, or `--cookies FILE` to import an existing session |
| `agentic-x status` | Check whether the persisted session is logged in, expired, or rate-limited |
| `agentic-x setup` | Provision the login browser into an isolated cache (requires `[browser]`) |
| `agentic-x doctor` | Authenticated round-trip + query-id freshness check (`--refresh` re-anchors query-ids from x.com's own JavaScript, browser-free, and names which rotated) |
| `agentic-x catalog` | Machine-readable JSON description of every command, argument and exit code (offline) |
| `agentic-x schema` | The output object schema; `--json` emits JSON Schema (offline) |
| `agentic-x feed` | Your home feed — takes no target, the feed belongs to the session |
| `agentic-x fetch <identifier>` | A profile's tweets (`--limit`, `--since`, `--until`, `--by screen_name\|id`, `--replies`†) — or another tab with `--tab posts\|replies\|media\|highlights\|articles` |
| `agentic-x bookmarks` | Your bookmarked posts — takes no target |
| `agentic-x likes` | Posts you have liked — takes no target (X made likes private in 2024) |
| `agentic-x list <identifier>` | A List's timeline, from an `x.com/i/lists/<id>` URL or the id |
| `agentic-x tweets <id>...` | Resolve many tweet ids in one request |
| `agentic-x profiles <handle>...` | Resolve many handles to profiles in one request |
| `agentic-x search <query>` | Tweets matching a query or advanced operators (`--product latest\|top\|media`) — or accounts with `--product people`, which emits `User` objects† |
| `agentic-x tweet <identifier>` | A single tweet plus its reply/conversation thread (`--replies`) |
| `agentic-x profile <identifier>` | One account's bio, counts, location and protected/verified state — emits a single `User` |
| `agentic-x following <identifier>` | Accounts a user follows — emits `User` objects |
| `agentic-x followers <identifier>` | Accounts following a user — emits `User` objects† (`--kind verified\|you-know` need **no** transaction id) |
| `agentic-x retweeters <tweet>` | Accounts that retweeted a tweet — emits `User` objects |

† Needs a generated `x-client-transaction-id` — see below.

All read commands share `--format json|ndjson`, `--output PATH`, `--profile NAME`, `--profile-dir PATH`, `--wait-on-limit`, `--max-wait`, `--raw` (+ `--no-redact`), and `-v/--verbose`. See the [CLI Reference](docs/wiki/CLI-Reference.md) for every flag and exit code — or just run `agentic-x catalog` for the same thing as JSON.

### The transaction-id wall, and how this package gets past it

Three operations — `SearchTimeline` (search), `UserTweetsAndReplies` (`fetch --replies`) and `Followers` — reject any request without a fresh `x-client-transaction-id` header. The header is **single-use**: replaying even a real captured one fails, because X's own client already spent it. So it cannot be harvested once and reused the way session cookies and query-ids are.

Since v0.3.0 this package **generates** that header per request, in pure Python, from ingredients x.com serves on its own home page (algorithm ported from the MIT-licensed [XClientTransaction](https://github.com/iSarabjitDhiman/XClientTransaction)). Verified working 2026-07-20.

**Be honest with yourself about this:** it is reverse-engineered, and X can invalidate it with any client deploy. It is the one part of this package where "it worked yesterday" is not evidence it works today. When it breaks, those three commands exit 4 with a clear message; everything else keeps working. `search` and `fetch --replies` additionally fall back to driving the stealth browser and reading the response X's own client receives (requires the `[browser]` extra) — that returns only the first page, and says so.

### What X no longer exposes

`likers` is not implemented. Note that the *reason* is not the one this README gave until v0.5.0: X's `Favoriters` operation **is** still in the JavaScript x.com serves (query id `39pAzSQtzG6pxX_AFnXXOw`, found 2026-07-26 by sweeping all 684 chunks). Calling it returns an envelope containing nothing but `TimelineTerminateTimeline` — X routes the request and hands back an empty, terminated timeline. The capability is gone even though the operation is not, so there is nothing here to re-enable. For quoters, use `agentic-x search "quoted_tweet_id:<id>"` — that is exactly what X's own /quotes tab does.

### Query-ids rot, and that is normal

X rotates its GraphQL query-ids every few weeks. The ids shipped in this package are a **fallback, not the source of truth** — seven of the nine shipped in v0.4.0 had rotted within six days. When a command starts returning exit 4 with "response envelope could not be parsed", run:

```bash
agentic-x doctor --refresh
```

That reads the current ids out of x.com's own JavaScript — including the lazily-loaded chunks where `HomeTimeline` and `Retweeters` live — writes them to your session, and tells you which ones had moved. No browser, no release, no waiting.

## Python API

```python
from agentic_x import XScraper

XScraper(profile="default").login()  # one-time, opens a headed browser

with XScraper(profile="default") as x:
    tweets = x.fetch_user_tweets("nasa", limit=50)
    for tweet in x.iter_user_tweets("nasa", limit=50):
        ...  # must be consumed inside the `with` block

    x.fetch_tweet("https://x.com/nasa/status/1234567890", replies=True)
    x.fetch_user_tab("nasa", tab="media", limit=20)
    x.fetch_home(limit=20)                  # your home feed
    x.fetch_bookmarks(limit=20)             # no target — the session's own
    x.fetch_likes(limit=20)                 # ditto; X made likes private in 2024
    x.fetch_list("https://x.com/i/lists/1418075522672771076", limit=20)
    x.fetch_tweets(["123", "456"])          # N ids, one request
    x.search("artemis", product="Latest")   # needs a generated transaction id
    x.fetch_user_tweets("nasa", replies=True, limit=50)

    # These return `User`, not `Tweet`.
    x.fetch_profile("nasa")                 # bio, counts, location, protected/verified
    x.fetch_profiles(["nasa", "spacex"])    # N handles, one request
    x.search_users("nasa", limit=20)        # find a handle from a name
    x.fetch_following("nasa", limit=100)
    x.fetch_followers("nasa", limit=100)    # needs a generated transaction id
    x.fetch_retweeters("1234567890", limit=100)
```

## Using this from Claude Code

`.claude/skills/x/SKILL.md` is a Claude Code skill that teaches Claude to drive these primitives and chain them into multi-hop exploration. It is checked in here as the source, but as a *project* skill it only loads in sessions opened inside this repo — which is the one place it should not fire, since working on this package is ordinary repo work. To actually use it, copy it to your user scope:

```bash
mkdir -p ~/.claude/skills/x && cp .claude/skills/x/SKILL.md ~/.claude/skills/x/SKILL.md
```

## Documentation

This README covers the essentials. For everything else, see the **[wiki](docs/wiki/README.md)**:

- [Installation](docs/wiki/Installation.md)
- [Quick Start](docs/wiki/Quick-Start.md)
- [CLI Reference](docs/wiki/CLI-Reference.md) — every flag, every exit code
- [Python API Reference](docs/wiki/Python-API-Reference.md)
- [Configuration](docs/wiki/Configuration.md) — profiles, environment variables
- [Output Schema](docs/wiki/Output-Schema.md) — every `Tweet`/`User`/`Media` field
- [Transaction-ID](docs/wiki/Transaction-ID.md) — why `search`, `fetch --replies` and `followers` are the fragile three
- [Security and Privacy](docs/wiki/Security-and-Privacy.md) — the full threat model behind [DISCLAIMER.md](DISCLAIMER.md)
- [FAQ and Troubleshooting](docs/wiki/FAQ-and-Troubleshooting.md)
- [Contributing](docs/wiki/Contributing.md)

## Contributing

Issues and pull requests are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for setup, tests, and the one rule that is specific to this project (never commit a real capture). Security reports go through [SECURITY.md](SECURITY.md), privately, never a public issue. Participation is covered by the [Code of Conduct](CODE_OF_CONDUCT.md).

## License

MIT — see [LICENSE](LICENSE). The license covers the code; it does not cover what you do with the data you collect (see [DISCLAIMER.md](DISCLAIMER.md)).
