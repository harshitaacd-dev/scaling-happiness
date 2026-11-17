"""Rebuild analysis inputs (tools.json, sources_full.json) from workbooks, using Final scores."""
import glob, json, os, sys, statistics, openpyxl
B = "."
WB, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
rows = json.load(open(f"{B}/corpus_in/rows.json")); hdr = rows[0]
corp = {r[hdr.index("tool_id")]: dict(zip(hdr, r)) for r in rows[1:]}
old = {t["name"]: t for t in json.load(open(f"{B}/results_in/tools.json"))}
old_src = json.load(open(f"{B}/results_in/sources_full.json"))
group = {s["tool"]: s["group"] for s in old_src}
KNOWN = {"Scoring table", "Sources to add", "Duplicates removed", "Missing full text", "Read me", "Excluded (not English)", "Element coding", "Master scores"}
STUDY = ("paper", "preprint", "conference", "case report", "book")
tools, srcs = [], []
for f in sorted(glob.glob(f"{WB}/*_extraction_table.xlsx")):
    tid = os.path.basename(f).replace("_extraction_table.xlsx", ""); name = corp[tid]["tool_name"]
    wb = openpyxl.load_workbook(f); ws = next(w for w in wb.worksheets if w.title not in KNOWN)
    per = []
    for c in range(3, ws.max_column + 1, 4):
        if not isinstance(ws.cell(1, c).value, int): continue
        sc = [ws.cell(26 + i, c + 2).value for i in range(29)]
        assert all(isinstance(x, int) for x in sc), (f, c)
        per.append((ws.cell(4, c).value, sc))
        srcs.append(dict(tool=name, group=group.get(name, ""), dev=old[name]["dev"], type=ws.cell(4, c).value, notes=ws.cell(10, c).value,
                         dp={ws.cell(13 + i, 2).value: [ws.cell(13 + i, c).value, ws.cell(13 + i, c + 1).value] for i in range(10)},
                         it={ws.cell(26 + i, 2).value: [ws.cell(26 + i, c).value, ws.cell(26 + i, c + 1).value, sc[i]] for i in range(29)}))
    items = [max((s[i] for _, s in per), default=0) for i in range(29)]
    tools.append(dict(name=name, group=old[name]["group"], n=len(per), total=sum(items), best_single=max((sum(s) for _, s in per), default=0),
                      mean_src=statistics.mean(sum(s) for _, s in per) if per else 0,
                      n_papers=sum(str(t).lower().startswith(STUDY) for t, _ in per), company=old[name]["company"], items=items, dev=old[name]["dev"]))
json.dump(tools, open(f"{OUT}/tools.json", "w"), ensure_ascii=False); json.dump(srcs, open(f"{OUT}/sources_full.json", "w"), ensure_ascii=False)
print(len(tools), "tools,", len(srcs), "sources")
for t in tools:
    o = old[t["name"]]
    if (t["n"], t["total"], t["best_single"], t["n_papers"]) != (o["n"], o["total"], o["best_single"], o["n_papers"]):
        print(f"  {t['name'][:40]}: sources {o['n']}->{t['n']}, total {o['total']}->{t['total']}, best {o['best_single']}->{t['best_single']}, studies {o['n_papers']}->{t['n_papers']}")
