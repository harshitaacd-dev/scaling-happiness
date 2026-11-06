"""Step 6: write one workbook per tool in the Niramai format, plus a cross-tool comparison workbook.

Per-tool workbooks go to output/<tool_id>_extraction_table.xlsx. If you have already entered Final scores in a
workbook, re-running this step keeps them out of harm's way: workbooks are only rebuilt with --rebuild, and the
comparison uses your Final scores where entered (otherwise the Preliminary scores).
Output: output/*.xlsx and output/comparison_by_sex_group.xlsx
"""
import csv
import json
import statistics
import sys
from collections import defaultdict

import openpyxl
from openpyxl.styles import Alignment, Font, PatternFill

from common import DATA, ROOT, load, safe_sheet_name, template_labels
from workbook import build

OUT = ROOT / "output"; OUT.mkdir(exist_ok=True)
DPS, ITEMS = template_labels()
# Sensitivity check: tools kept in the corpus whose only public evidence is promotional (press release or launch
# article). The comparison is reported with and without them. Matched on company name, case-insensitive.
SENSITIVITY_EXCLUDE = ["lord's mark", "telerad"]
TYPE_ORDER = ["paper", "preprint", "conference paper", "conference abstract", "book chapter", "case report", "trial registration", "patent", "magazine feature", "web page"]


def type_rank(t):
    t = (t or "").lower()
    return next((i for i, k in enumerate(TYPE_ORDER) if k in t), len(TYPE_ORDER))


def tool_sources(tid, recs):
    rows = []
    for r in recs:
        p = DATA / "extractions" / f"{r.get('source_id')}.json"
        if r.get("source_id") and p.exists() and r.get("decision") in ("Include", "Borderline"):
            e = json.loads(p.read_text())
            rows.append((r, e))
    rows.sort(key=lambda x: (type_rank(x[1]["source_type"]), str(x[1]["year"])))
    # same study: sources that cite the same registration number
    ids = [set(i.strip() for i in e["registration_ids"].split(";") if i.strip() and i.strip().lower() != "none") for _, e in rows]
    out = []
    for k, (r, e) in enumerate(rows):
        same = [f"No. {j + 1}" + (" (registration)" if "trial" in rows[j][1]["source_type"].lower() else "")
                for j in range(len(rows)) if j != k and ids[k] & ids[j]]
        file_used = r.get("manual_pdf") or r.get("url") or ""
        out.append(dict(company=e["company"], tool=e["ai_tool"], type=e["source_type"], title=e["title"] or r["title"], authors=e["authors"],
                        year=e["year"], file=file_used, same="; ".join(same) or None,
                        notes=f"{e['extraction_notes']} Full text: {r.get('fulltext_status', '')}. Unverified quotes: {e['_unverified_quotes']}.",
                        dp=e["_rendered"]["dp"], items=e["_rendered"]["items"], sid=r["source_id"]))
    return out


def readme(t, n, missing):
    return [
        f"{t['tool_name']} ({t['company']}) sources only. Cancer: {t['cancer_types']}. Group: {t['sex_group']}. Purpose: {t['purpose']}.",
        "Sources were found by scripted searches of Europe PMC, PubMed, Crossref, ClinicalTrials.gov and WHO ICTRP (CTRI), plus a web search for "
        "company and grey-literature pages, and screened with the Niramai rule: a study of the tool or a document by its company, with full text.",
        "Each extraction sheet has two tables. Table 1 — Data points: Value and verbatim supporting quote (page); descriptive, not scored. "
        "Table 2 — the 29 STANDING Together items: Value, verbatim supporting quote (page), Final score (grey, left empty for you) and Preliminary score (0/1/2).",
        "The 'Scoring table' sheet holds the scores with totals by formula (Part 1 max 36, Part 2 max 22, overall max 58).",
        "Score key: 0 = no information, 1 = partial information, 2 = complete information. Preliminary scores are Claude's; the Final score is yours.",
        "Every quote was checked against the source text by script. Quotes marked '[check: quote not found verbatim]' could not be matched and must be checked by hand.",
        "'Same study as' links sources that cite the same trial registration number. Page numbers refer to the PDF page; registries and web pages have none.",
        f"Sources completed: {n}. Sources without full text: {missing} (listed in 'Missing full text').",
    ]


def final_or_prelim(path, sheet, n):
    """Per-source item scores from an existing workbook: Final score where entered, else Preliminary."""
    wb = openpyxl.load_workbook(path, data_only=True)
    known = {"Scoring table", "Sources to add", "Duplicates removed", "Missing full text", "Read me"}
    ws = wb[sheet] if sheet in wb.sheetnames else next(w for w in wb.worksheets if w.title not in known)
    scores = []
    for k in range(n):
        cf, cp = 3 + 4 * k + 2, 3 + 4 * k + 3
        scores.append([ws.cell(26 + i, cf).value if isinstance(ws.cell(26 + i, cf).value, (int, float)) else (ws.cell(26 + i, cp).value or 0) for i in range(29)])
    return scores


if __name__ == "__main__":
    rebuild = "--rebuild" in sys.argv
    corpus = {t["tool_id"]: t for t in csv.DictReader(open(DATA / "corpus.csv", encoding="utf-8-sig"))}
    sources = load("sources.json")
    summary = []
    for tid, recs in sources.items():
        t = corpus[tid]
        srcs = tool_sources(tid, recs)
        missing = [[f"{r['title']} ({r.get('trial_id') or r.get('doi') or r.get('url', '')})", r.get("fulltext_status", "")]
                   for r in recs if r.get("decision") in ("Include", "Borderline") and not r.get("text_file")]
        co = t["company"].split("/")[0].strip()
        sno = {x["sid"]: k + 1 for k, x in enumerate(srcs)}
        title_of = {x["sid"]: x["title"] for x in srcs}
        dups = [[f"{r['title']} ({r.get('url', '')})", f"No. {sno.get(r['duplicate_of'], '?')}: {title_of.get(r['duplicate_of'], r['duplicate_of'])}",
                 "Same text as a source already in the workbook (republished copy)"] for r in recs if r.get("decision") == "Duplicate"]
        sheet = next((x for x in (f"{co} ({t['tool_name']})", f"{co.split()[0]} ({t['tool_name']})", t["tool_name"]) if len(x) <= 31), t["tool_name"])
        sheet = safe_sheet_name(sheet)
        fname = f"{tid}_extraction_table.xlsx"
        spec = dict(sheet=sheet, file=fname, sources=srcs, dups=dups, missing=missing, to_add=[], readme=readme(t, len(srcs), len(missing)))
        if rebuild or not (OUT / fname).exists():
            build(spec, OUT)
        scores = final_or_prelim(OUT / fname, sheet, len(srcs)) if srcs else []
        tool_level = [max((s[i] for s in scores), default=0) for i in range(29)]  # best disclosure across all public sources
        summary.append(dict(t=t, n=len(srcs), missing=len(missing), items=tool_level, total=sum(tool_level)))
        print(f"{t['tool_name'][:40]:40s} sources={len(srcs):3d} missing={len(missing):3d} tool score={sum(tool_level)}/58")

    # ---------------- comparison workbook
    wb = openpyxl.Workbook(); H = Font(bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="1F4E78")
    ws = wb.active; ws.title = "Tool scores"
    ws.append(["Tool", "Company", "Cancer", "Sex group", "Purpose", "Sources extracted", "Sources without full text", "Total (of 58)", "% of maximum",
               "Items reported (score > 0, of 29)"] + [lab for _, lab in ITEMS])
    for s in sorted(summary, key=lambda s: (s["t"]["sex_group"], -s["total"])):
        t = s["t"]
        ws.append([t["tool_name"], t["company"], t["cancer_types"], t["sex_group"], t["purpose"], s["n"], s["missing"], s["total"],
                   round(s["total"] / 58, 3), sum(x > 0 for x in s["items"])] + s["items"])
    def group_table(sheet, rows_in, title):
        groups = defaultdict(list)
        for s_ in rows_in:
            if s_["n"]:
                groups[s_["t"]["sex_group"]].append(s_)
        order = [k for k in ("women-specific", "men-specific", "all") if k in groups]
        sheet.append([title] + order)
        sheet.append(["Tools with at least one extracted source"] + [len(groups[k]) for k in order])
        sheet.append(["Mean total score (of 58)"] + [round(statistics.mean(x["total"] for x in groups[k]), 1) for k in order])
        sheet.append(["Median total score (of 58)"] + [statistics.median(x["total"] for x in groups[k]) for k in order])
        sheet.append(["Mean items reported (of 29)"] + [round(statistics.mean(sum(v > 0 for v in x["items"]) for x in groups[k]), 1) for k in order])
        sheet.append([])
        sheet.append(["% of tools reporting each item (score > 0)"] + order)
        for i, (_, lab) in enumerate(ITEMS):
            sheet.append([lab] + [round(sum(x["items"][i] > 0 for x in groups[k]) / len(groups[k]), 2) for k in order])

    g = wb.create_sheet("Group comparison")
    group_table(g, summary, "All included tools")
    excl = [s_ for s_ in summary if any(e in s_["t"]["company"].lower() for e in SENSITIVITY_EXCLUDE)]
    sg = wb.create_sheet("Sensitivity check")
    group_table(sg, [s_ for s_ in summary if s_ not in excl], "Excluding promotional-only tools: " + ", ".join(x["t"]["tool_name"] for x in excl))
    n = wb.create_sheet("Read me")
    for l in ["Tool-level score per item = the highest score that item reaches in any of the tool's public sources (Final score where you entered one, otherwise Claude's preliminary score).",
              "Groups: women-specific = breast, cervical, ovarian, uterine cancers; men-specific = prostate, testicular; all = cancers that affect everyone.",
              "Tool numbers per group are small, so compare descriptively; differences may also reflect company size, regulation or the number of sources.",
              "'Sensitivity check' repeats the comparison without the tools whose only public evidence is promotional (see SENSITIVITY_EXCLUDE in s6_build_workbooks.py). Report both.",
              "Re-run 'python s6_build_workbooks.py' after entering Final scores to refresh this comparison."]:
        n.append([l])
    for sh in (ws, g, sg):
        for c in sh[1]: c.font = H; c.fill = HF; c.alignment = Alignment(wrap_text=True, vertical="top")
        sh.column_dimensions["A"].width = 45; sh.freeze_panes = "B2"
    n.column_dimensions["A"].width = 140
    wb.save(OUT / "comparison_by_sex_group.xlsx")
    print("written: output/comparison_by_sex_group.xlsx")
