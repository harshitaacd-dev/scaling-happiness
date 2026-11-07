"""Where are we? One report on the whole pipeline, per tool and in total.

    python status.py

Shows, for every included tool: sources included, full texts ready, papers and other sources still missing,
duplicate copies set aside, sources already extracted (step 5), quotes to check, and workbook status (step 6).
Also writes the same table to data/status.csv so you can open it in Excel or Numbers.
"""
import csv
import json
from collections import defaultdict

from common import DATA, ROOT, load

if __name__ == "__main__":
    corpus = {t["tool_id"]: t for t in csv.DictReader(open(DATA / "corpus.csv", encoding="utf-8-sig"))}
    sources = load("sources.json", {})
    ext_dir = DATA / "extractions"
    rows = []
    for tid, recs in sources.items():
        t = corpus.get(tid, {})
        live = [r for r in recs if r.get("decision") in ("Include", "Borderline")]
        texts = [r for r in live if r.get("text_file")]
        extracted, to_check = 0, 0
        for r in texts:
            p = ext_dir / f"{r.get('source_id')}.json"
            if p.exists():
                extracted += 1
                try:
                    to_check += json.loads(p.read_text()).get("_unverified_quotes", 0)
                except Exception:
                    pass
        rows.append({
            "tool": t.get("tool_name", tid), "company": t.get("company", ""), "sex_group": t.get("sex_group", ""),
            "sources included": len(live),
            "full texts ready": len(texts),
            "papers missing": sum(1 for r in live if not r.get("text_file") and r["kind"] == "publication"),
            "other missing": sum(1 for r in live if not r.get("text_file") and r["kind"] != "publication"),
            "duplicates set aside": sum(1 for r in recs if r.get("decision") == "Duplicate"),
            "extracted (step 5)": extracted,
            "still to extract": len(texts) - extracted,
            "quotes to check": to_check,
            "workbook (step 6)": "yes" if (ROOT / "output" / f"{tid}_extraction_table.xlsx").exists() else "no",
        })
    rows.sort(key=lambda r: (r["sex_group"], r["tool"]))

    cols = ["sources included", "full texts ready", "papers missing", "other missing", "duplicates set aside",
            "extracted (step 5)", "still to extract", "quotes to check"]
    short = {"sources included": "incl", "full texts ready": "text", "papers missing": "pap-", "other missing": "oth-",
             "duplicates set aside": "dup", "extracted (step 5)": "done", "still to extract": "todo", "quotes to check": "chk"}
    print(f"\n{'tool':34s} {'group':15s} " + " ".join(f"{short[c]:>5s}" for c in cols) + "  book")
    groups = defaultdict(lambda: defaultdict(int))
    for r in rows:
        print(f"{r['tool'][:34]:34s} {r['sex_group'][:15]:15s} " + " ".join(f"{r[c]:5d}" for c in cols) + f"  {r['workbook (step 6)']}")
        for c in cols:
            groups[r["sex_group"]][c] += r[c]; groups["ALL TOOLS"][c] += r[c]
        groups[r["sex_group"]]["tools"] += 1; groups["ALL TOOLS"]["tools"] += 1
    print("\n" + "-" * 100)
    for g in sorted(k for k in groups if k != "ALL TOOLS") + ["ALL TOOLS"]:
        v = groups[g]
        print(f"{g + ' (' + str(v['tools']) + ' tools)':50s} " + " ".join(f"{v[c]:5d}" for c in cols))
    a = groups["ALL TOOLS"]
    print("\nKey: incl = sources included | text = full texts ready | pap- / oth- = papers / other sources missing |"
          " dup = duplicates set aside | done = extracted | todo = still to extract | chk = quotes to check by hand")
    print(f"\nNext: ", end="")
    if a["still to extract"]:
        print(f"{a['still to extract']} sources still to extract  ->  python s5_extract.py")
    elif not all(r["workbook (step 6)"] == "yes" for r in rows):
        print("build the workbooks  ->  python s6_build_workbooks.py")
    else:
        print("all extracted and built. Check the quotes marked [check: ...] and enter your Final scores.")
    with open(DATA / "status.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("Saved as data/status.csv")
