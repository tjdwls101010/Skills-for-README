"""코퍼스 전체에 스킬의 지표 모듈을 돌려 계층별 표를 만든다.

이 파일이 research/metrics-summary.md의 표를 낸다. 스킬과 같은 코드를 부르므로
지표 정의가 바뀌면 표도 함께 바뀐다.

사용: 레포 루트에서 `python3 research/aggregate_corpus.py` (.tmp/에 원문이 있어야 한다)"""
import json, statistics, sys
from pathlib import Path
sys.path.insert(0, ".claude/skills/repo-showcase/scripts")
from showcase import readme_metrics, first_screen, blockers
from showcase.github import RepoFacts

man = json.load(open(".tmp/readmes/manifest.json"))
rows = []
for r in man:
    path = Path(".tmp/readmes") / (r["repo"].replace("/", "__") + ".md")
    text = path.read_text(encoding="utf-8", errors="replace")
    m = readme_metrics.analyze(text)
    fs = first_screen.analyze(text)
    pf = r["profile_files"]
    rows.append(dict(
        repo=r["repo"], tier=r["tier"], lines=m.lines, words=m.words, badges=m.badges,
        first_result_image=m.first_result_image_line, install=m.install_heading_line,
        first_code=m.first_code_line,
        one_liner_line=fs.one_liner.line if fs.one_liner else None,
        one_liner_len=fs.one_liner.length if fs.one_liner else None,
        alternatives=bool(fs.one_liner and fs.one_liner.alternatives),
        evidence=sorted({e.kind for e in fs.evidence}),
        first_screen_evidence=any(e.line <= 40 for e in fs.evidence),
        desc_len=len(" ".join((r["description"] or "").split())),
        desc_truncated=len(" ".join((r["description"] or "").split())) > 137,
        topics=len(r["topics"]), license=bool(pf["license"]),
        security=bool(r["has_security"]), coc=bool(pf["code_of_conduct_file"]),
        contrib=bool(pf["contributing"]),
    ))

early = json.load(open(".tmp/readmes_early/manifest.json"))
erows = []
for e in early:
    path = Path(".tmp/readmes_early") / (e["repo"].replace("/", "__") + f"__m{e['months_after_creation']}.md")
    text = path.read_text(encoding="utf-8", errors="replace")
    m = readme_metrics.analyze(text)
    fs = first_screen.analyze(text)
    erows.append(dict(repo=e["repo"], m=e["months_after_creation"], lines=m.lines, words=m.words,
                      badges=m.badges, first_result_image=m.first_result_image_line,
                      install=m.install_heading_line,
                      one_liner_line=fs.one_liner.line if fs.one_liner else None,
                      one_liner_len=fs.one_liner.length if fs.one_liner else None,
                      alternatives=bool(fs.one_liner and fs.one_liner.alternatives),
                      first_screen_evidence=any(ev.line <= 40 for ev in fs.evidence)))

def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs)) if xs else None

def block(name, rs, n_total=None):
    n = len(rs)
    return dict(
        tier=name, n=n, lines=med(r["lines"] for r in rs), words=med(r["words"] for r in rs),
        badges=med(r["badges"] for r in rs),
        first_result_image=med(r["first_result_image"] for r in rs),
        no_result_image=sum(1 for r in rs if r["first_result_image"] is None),
        install=med(r["install"] for r in rs),
        first_screen_evidence=f"{sum(1 for r in rs if r['first_screen_evidence'])}/{n}",
        one_liner_line=med(r["one_liner_line"] for r in rs),
        one_liner_len=med(r["one_liner_len"] for r in rs),
        alternatives=f"{sum(1 for r in rs if r['alternatives'])}/{n}",
        desc_len=med(r.get("desc_len") for r in rs) if "desc_len" in rs[0] else None,
        desc_truncated=f"{sum(1 for r in rs if r.get('desc_truncated'))}/{n}" if "desc_len" in rs[0] else None,
        license=f"{sum(1 for r in rs if r.get('license'))}/{n}" if "license" in rs[0] else None,
        security=f"{sum(1 for r in rs if r.get('security'))}/{n}" if "license" in rs[0] else None,
        coc=f"{sum(1 for r in rs if r.get('coc'))}/{n}" if "license" in rs[0] else None,
        contrib=f"{sum(1 for r in rs if r.get('contrib'))}/{n}" if "license" in rs[0] else None,
    )

out = [block(t, [r for r in rows if r["tier"] == t]) for t in
       ("mega", "classic_solo", "trendshift", "low_traction", "owner")]
for months in (3, 9):
    out.append(block(f"classic_solo m{months}", [r for r in erows if r["m"] == months]))
# 같은 12개의 현재
subset = {e["repo"] for e in early}
out.append(block("classic_solo 현재(같은 12개)", [r for r in rows if r["repo"] in subset]))

json.dump({"tiers": out, "rows": rows, "early": erows},
          open(".tmp/metrics_corrected.json", "w"), ensure_ascii=False, indent=2)
keys = ["tier","n","lines","words","badges","first_result_image","no_result_image","install",
        "first_screen_evidence","one_liner_line","one_liner_len","alternatives",
        "desc_len","desc_truncated","license","security","coc","contrib"]
print(" | ".join(keys))
for b in out:
    print(" | ".join(str(b.get(k)) for k in keys))
