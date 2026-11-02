"""Apply screening rules/overrides and write the search results workbook."""
import json, re, sys
from collections import Counter, defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

d = json.load(open(sys.argv[1])); OUT = sys.argv[2]
tools = {t["id"]: t for t in d["tools"]}
AI = r"artificial intelligence|\bAI\b|automat|machine learning|deep learning|computer[- ]assisted|algorithm|neural"
CLIN = r"cervi|breast|mammo|colposcop|VIA\b|pap\b|cytolog|thermo"

# Manual overrides after reading titles (key: substring of title or ID -> (decision, reason))
OVERRIDES = [
    ("special needs", "Exclude", "Name clash: CanAssist assistive-technology programme, not OncoStem"),
    ("ASSISTIVE TECHNOLOGIES FOR OLDER", "Exclude", "Name clash: CanAssist assistive-technology programme, not OncoStem"),
    ("MedXAI: A Retrieval-Augmented", "Exclude", "Name clash: unrelated MedXAI software framework, not the CTRI cervical tool"),
    ("MedXAI-MM", "Exclude", "Name clash: unrelated MedXAI software framework, not the CTRI cervical tool"),
    ("PD-L1 in NSCLC", "Exclude", "uPath used for lung PD-L1, not HER2 breast"),
    ("Ayrshire cattle", "Exclude", "Unrelated full-text hit"),
    ("Concept of personality", "Exclude", "Unrelated full-text hit"),
    ("Leptomeningeal", "Exclude", "Unrelated PubMed hit"),
    ("Glioblas", "Exclude", "Unrelated PubMed hit"),
    ("Enumeration of Ki67", "Check", "OptraSCAN product used, but not CytoSiA (cervical cytology); likely exclude"),
    ("Plasma Cell Quantification", "Check", "OptraSCAN product used, but not CytoSiA; likely exclude"),
]

def decide(o):
    title = o["title"]; t0 = o["tool_ids"][0]
    for k, dec, why in OVERRIDES:
        if k.lower() in title.lower(): return dec, why
    sug, why = o["suggestion"], o["reason"]
    if sug == "Already in library": return sug, why
    if o["kind"] == "trial registration" and sug != "Include":
        if re.search(CLIN, title, re.I) and re.search(AI, title, re.I): return "Check", "Registry hit on breast/cervical AI; tool not named in title, may be the same tool"
        if re.search(CLIN, title, re.I) and t0 in ("T01", "T10"): return "Check", "Registry hit on breast screening; may be the same tool"
        return "Exclude", "Registry keyword hit unrelated to breast/cervical AI"
    if "T05" in o["tool_ids"] and sug == "Include" and not re.search(AI + r"|visual ?check", title + " " + o["abstract"], re.I):
        return "Check", "Uses the MobileODT EVA camera/colposcope; the AI (VisualCheck) may not be evaluated"
    if "T07" in o["tool_ids"] and sug != "Exclude":
        return "Check", "AIIMS search is not tool-specific; keep only if it is the AIIMS/BPL mammography model"
    return sug, why

rows = []
for o in d["items"]:
    dec, why = decide(o)
    if dec == "Include" and o["india"] != "Yes" and set(o["tool_ids"]) & {"T03", "T04", "T05", "T10", "T12"}:
        why += "; no India mention in title/abstract (study may be outside India)"
    o["decision"], o["why"] = dec, why
    o["ident"] = o["trial_id"] or (f'doi:{o["doi"]}' if o["doi"] else (f'PMID:{o["pmid"]}' if o["pmid"] else ""))
    rows.append(o)

wb = Workbook()
H = Font(bold=True, color="FFFFFF"); HF = PatternFill("solid", fgColor="1F4E78"); WR = Alignment(wrap_text=True, vertical="top")

def sheet(name, header, data, widths):
    ws = wb.create_sheet(name); ws.append(header)
    for c in ws[1]: c.font = H; c.fill = HF; c.alignment = WR
    for r in data: ws.append(r)
    for i, w in enumerate(widths, 1): ws.column_dimensions[get_column_letter(i)].width = w
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment = WR
    ws.freeze_panes = "A2"; ws.auto_filter.ref = ws.dimensions
    return ws

REC_H = ["Tool", "Type", "Year", "Title", "Authors / sponsor", "Journal / registry", "ID", "Open access", "Link", "India in title/abstract",
         "Where tool is mentioned", "Found in", "Suggested decision", "Reason", "YOUR DECISION", "Abstract / summary"]
def rec(o):
    return [o["tools"], o["kind"], o["year"], o["title"], o["authors"], o["venue"], o["ident"], o["open_access"], o["link"], o["india"],
            o["mention"], o["databases"], o["decision"], o["why"], "", o["abstract"]]
W = [24, 14, 7, 60, 28, 24, 26, 10, 30, 10, 18, 20, 16, 40, 14, 60]
order = lambda o: (o["tool_ids"][0], o["kind"], str(o["year"]))

# README
ws = wb.active; ws.title = "Read me"
c = Counter(o["decision"] for o in rows)
total_hits = sum((l["retrieved"] or 0) for l in d["log"])
lines = [
    "Literature and trial-registration search: AI breast and cervical cancer screening tools in India",
    f"Search date: {d['date']}",
    "",
    "DATABASES: Europe PMC (includes PubMed/MEDLINE, PMC full text, preprints, conference abstracts); PubMed; Crossref; ClinicalTrials.gov; WHO ICTRP (which aggregates CTRI and 16 other registries).",
    "Europe PMC searches titles, abstracts AND full text, so it also finds papers (e.g. reviews) that mention a tool only in the body text.",
    "Every query, with hit counts, is in the 'Search log' sheet. The search script is reproducible and can be re-run on any date.",
    "",
    "TOOLS AND TERMS:",
] + [f"  {t['id']} {t['label']}: databases: {' | '.join(t['queries'])}; registries/Crossref: {' | '.join(t['reg_terms'])}" for t in d["tools"]] + [
    "",
    "FLOW (PRISMA-style):",
    f"  Records retrieved across all queries: {total_hits}",
    f"  Unique records after deduplication (DOI, PMID, trial ID, title): {len(rows)}",
    f"  Already in your library (S01-S62): {c['Already in library']}",
    f"  Suggested include (new): {c['Include']}",
    f"  To check (uncertain): {c['Check']}",
    f"  Secondary (tool mentioned only in full text, e.g. reviews): {c['Check (secondary)']}",
    f"  Excluded automatically or after title check (name clashes, unrelated registry hits): {c['Exclude']}",
    "",
    "SUGGESTED DECISION RULE: include if the source names the tool (or its company) and reports something about the tool's data or performance.",
    "Suggested decisions are a first pass from titles/abstracts only. Fill in YOUR DECISION (Include / Exclude) on each sheet.",
    "",
    "NOT COVERED BY THIS SEARCH (see 'Still to search'): direct CTRI website, Google Patents, company websites/press, paywalled full texts.",
    "Caveat: your separate Niramai library (50 sources) is not in this comparison, so some 'new' Thermalytix records may already be in it.",
]
for l in lines: ws.append([l])
ws.column_dimensions["A"].width = 150; ws["A1"].font = Font(bold=True, size=13)

# Summary by tool
summ = []
for tid, t in tools.items():
    tr = [o for o in rows if tid in o["tool_ids"]]; cc = Counter(o["decision"] for o in tr)
    inc = [o for o in tr if o["decision"] == "Include"]
    summ.append([t["label"], len(tr), cc["Already in library"], cc["Include"], sum(o["kind"] == "trial registration" for o in inc),
                 sum(o["open_access"] == "Yes" for o in inc), sum(o["india"] == "Yes" for o in inc), cc["Check"], cc["Check (secondary)"], cc["Exclude"]])
sheet("Summary by tool", ["Tool", "Unique records", "Already in library", "NEW: suggested include", "...of which trial registrations",
      "...of which open access", "...of which mention India", "To check", "Secondary (full-text mention)", "Excluded"], summ, [34, 10, 10, 12, 12, 12, 12, 10, 12, 10])

dv = DataValidation(type="list", formula1='"Include,Exclude,Unsure"', allow_blank=True)
for name, dec in [("NEW - Include", "Include"), ("To check", "Check"), ("Secondary (full text)", "Check (secondary)"),
                  ("Already in library", "Already in library"), ("Excluded", "Exclude")]:
    data = [rec(o) for o in sorted((o for o in rows if o["decision"] == dec), key=order)]
    if dec == "Already in library":
        hdr = ["Your S-number"] + REC_H[:13]; data = [[o["existing"]] + rec(o)[:13] for o in sorted((o for o in rows if o["decision"] == dec), key=lambda o: o["existing"])]
        sheet(name, hdr, data, [10] + W[:13])
    else:
        s = sheet(name, REC_H, data, W); s.add_data_validation(dv) if name == "NEW - Include" else None
        if name == "NEW - Include": dv.add(f"O2:O{len(data)+1}")

# library sources not found by the search (expected: web pages, patents)
lib = json.load(open(sys.argv[3])); found = {o["existing"] for o in rows if o["existing"]}
sheet("Library not re-found", ["S-number", "Tool", "Type", "Title", "Why probably not found"],
      [[s, v["tool"], v["type"], v["title"], {"web_page": "Web page: not indexed in scholarly databases", "patent": "Patent: not searched (Google Patents)"}.get(v["type"], "Check: database coverage, or title differs")]
       for s, v in sorted(lib.items()) if s not in found], [10, 28, 16, 70, 45])

sheet("Search log", ["Date", "Database", "Tool ID", "Tool", "Query", "Hits reported", "Records retrieved", "Note"],
      [[l["date"], l["database"], l["tool_id"], tools[l["tool_id"]]["label"], l["query"], l["hits"], l["retrieved"], l["note"]] for l in d["log"]],
      [11, 18, 8, 30, 60, 10, 10, 50])

sheet("Still to search", ["Source", "Why", "How"], [
    ["CTRI website (ctri.nic.in)", "ICTRP covers CTRI, but full CTRI records hold more detail (sample size, sites, ethics, status)", "Open each included CTRI ID on your Mac and save the page as PDF"],
    ["Google Patents", "Company patents can describe training data (Niramai has 3)", "Search assignee: Niramai, Periwinkle, Aindra, OncoStem, UE LifeSciences, OptraSCAN, MobileODT, Telerad"],
    ["Company websites and press", "Lord's Mark, MammoAssist, CervAstra have no scholarly record; web pages are their only disclosure", "Save the product, publications and FAQ pages for each tool"],
    ["Paywalled full texts", "Open-access ones download freely; the rest need the EUR library proxy", "Use browser_download_eur.py on the included rows with Open access = No/unknown"],
    ["Regulatory: CDSCO lists, FDA 510(k)/De Novo, CE", "Foreign regulator summaries sometimes describe validation data", "Check iBreastExam (FDA cleared), uPath (FDA/CE), MobileODT EVA (FDA)"],
], [32, 60, 70])

wb.save(OUT)
print(Counter(o["decision"] for o in rows)); print(*summ, sep="\n")
