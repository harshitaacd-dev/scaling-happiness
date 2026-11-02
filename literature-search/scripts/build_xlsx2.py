"""Workbook for the verification search (search 2)."""
import json, sys
from collections import Counter
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

d = json.load(open(sys.argv[1])); OUT = sys.argv[2]
items = d["items"]

# manual notes after reading titles
NOTES = {
    "CTRI/2021/08/036015": ("Include", "EVA VisualCheck (MobileODT)", "Indian trial of the MobileODT AI. Missed by search 1 because the registry spells it 'Mobile ODT'. Your only India-specific evidence for EVA's AI"),
    "Paving the Way to New Low-Cost": ("Include", "", "Book chapter on AVE development"),
    "Automatic Detection of Oral Lesion": ("Exclude", "", "Same NCI group, but oral cancer, not cervical AVE"),
    "Real-world data of CanAssist Breast-first": ("Already in library", "", "Same paper as S04/S19 (title punctuation differs)"),
}
CANDIDATES = [
    ("PredAID-CERVIA (AI cervical screening)", "CTRI/2022/05/042719; CTRI/2022/06/043030; CTRI/2022/08/044703", "Three Indian trials (2022) of a named AI cervical screening tool, including rural women and female sex workers", "Strong candidate: named tool, AI, screening, India. Check sponsor/company and any publications"),
    ("MammoAlert (Pandora CDx)", "CTRI/2017/05/008716", "Blood test for breast cancer screening", "Already on your borderline list. A blood test; include only if its result relies on an AI/ML algorithm"),
    ("AI breast density / BI-RADS software", "CTRI/2026/10/118914", "AI software to measure breast density and assign BI-RADS on mammograms", "Candidate: check sponsor; may be a commercial product (2026)"),
    ("Smartphone-based cervical device", "CTRI/2022/02/040066", "Clinical testing of a smartphone-based device for early cervical cancer diagnosis", "Check whether AI is used and whether it is a named product"),
    ("LED-based cervical screening device", "CTRI/2025/02/081202", "LED-based device to screen cervical cancer by studying cervical tissue", "Check whether AI/algorithm is used"),
    ("AI cervical cancer detection", "CTRI/2021/03/032299", "Role of artificial intelligence in detecting cervical cancer", "Check: may be an academic model or a known tool"),
    ("Mammogram decision support system", "CTRI/2022/11/047369", "Design and development of a decision support system for breast cancer detection from mammograms", "Likely academic; check sponsor"),
    ("Computer device for breast assessment", "CTRI/2023/03/050666", "Assessing breast cancer using a computer device vs traditional methods", "Check: could be Thermalytix or iBreastExam under a generic title"),
    ("New breast early-detection device", "CTRI/2018/09/015759", "Evaluation of a new device for early detection of breast cancer", "Check: could be Thermalytix or iBreastExam under a generic title"),
    ("Cervical inspection device", "CTRI/2017/07/009005", "Inspection device for cervical cancer screening", "Check: could be an early Smart Scope study"),
    ("Bimodal cervical imaging", "CTRI/2020/09/027999", "Cervical cancer detection using a bimodal imaging technique", "Check whether AI is used"),
    ("2PCubeHealth", "CTRI/2024/02/062417", "Project for early detection of cancer", "Check cancer type and AI use"),
    ("TruScreen", "CTRI/2020/01/022650", "TruScreen vs Pap smear for cervical screening", "Borderline: optoelectronic device with an automated classification algorithm; decide if it counts as AI"),
    ("CanScan Breath Test", "CTRI/2025/12/099452; CTRI/2025/12/099573", "Breath test for screening breast cancer", "Borderline: check whether the classifier is ML-based"),
    ("Android cytology app (CliniMed LifeSciences?)", "doi:10.31557/apjcp.2026.27.2", "Diagnostic accuracy of cervical cell morphologies from Android-captured cytopathology images", "Check whether this is a named commercial product"),
]
for o in items:
    for k, (dec, tool, note) in NOTES.items():
        if k in (o["ident"] or "") or k.lower() in o["title"].lower():
            o["decision"], o["why"] = dec, note
            if tool: o["tool"] = tool

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

c = Counter(o["decision"] for o in items)
logs = d["log"]
def strat_total(prefix): return sum((l["retrieved"] or 0) for l in logs if l["strategy"].startswith(prefix))
ws = wb.active; ws.title = "Read me"
for l in [
    "Verification search (search 2): checking that search 1 missed nothing",
    f"Search date: {d['date']}",
    "",
    "STRATEGIES:",
    f"  A. Spelling and name variants in Europe PMC (e.g. SmartScope, Smart-Scope, Niramai Health Analytix, Aindra Systems, UE Life Sciences): {strat_total('A')} records",
    "  B. Semantic Scholar and OpenAlex: NOT RUN. Both APIs were rate-limited from this cloud session. Re-run from your own computer or with free API keys.",
    f"  C. Citation chasing: forward citations and reference lists of every known paper (Europe PMC), keeping titles that name a tool: {strat_total('C')} records",
    f"  D. Topic search not tied to tool names: AI + breast/cervical + screening + India (Europe PMC); AI/thermography + breast/cervical in India (ClinicalTrials.gov); 15 topic terms in WHO ICTRP, CTRI records only: {strat_total('D')} records",
    "",
    "Only records NOT already found by search 1 or held in your library (S01-S62) are listed here.",
    f"  New unique records: {len(items)}",
    f"  NEW - Include (tool named in title/abstract): {c['Include']}",
    f"  Candidate new tools (curated from trial registries): {len(CANDIDATES)}",
    f"  To check: {c['Check'] + c['Check: possible other tool']}",
    f"  Topic only (Indian AI screening research with no product named, mostly academic models): {c['Topic only']}",
    f"  Secondary (variant term only in full text): {c['Secondary (full text)']}",
    "",
    "MAIN FINDINGS:",
    "  1. Search 1 coverage of the literature was good: only 9 new tool-naming records, mostly conference papers and a book chapter.",
    "  2. Trial registries were the gap. An Indian CTRI trial of MobileODT's AI was missed (registered as 'Mobile ODT').",
    "  3. Several Indian AI screening tools in CTRI are not on your tool list (see 'Candidate new tools'). PredAID-CERVIA is the strongest.",
    "  4. Most AI breast/cervical research from India is academic models tested on public datasets, not deployed tools.",
]: ws.append([l])
ws.column_dimensions["A"].width = 150; ws["A1"].font = Font(bold=True, size=13)

sheet("Candidate new tools", ["Possible tool", "Registration / ID", "What the record says", "Suggested action", "YOUR DECISION"],
      [list(x) + [""] for x in CANDIDATES], [32, 40, 60, 60, 14])
H2 = ["Tool", "Type", "Year", "Title", "Authors / sponsor", "Journal / registry", "ID", "Open access", "Link", "India mentioned", "Strategy", "Found in", "Found via (citations)", "Suggested decision", "Reason", "YOUR DECISION", "Abstract"]
def rec(o): return [o["tool"], o["kind"], o["year"], o["title"], o["authors"], o["venue"], o["ident"], o["open_access"], o["link"], o["india"], o["strategy"], o["found_in"], o["via"], o["decision"], o["why"], "", o["abstract"]]
W = [24, 12, 7, 60, 26, 22, 26, 10, 30, 9, 12, 18, 24, 16, 40, 14, 60]
key = lambda o: (o["tool"], o["kind"], str(o["year"]))
for name, decs in [("NEW - Include", {"Include"}), ("To check", {"Check", "Check: possible other tool"}), ("Topic only", {"Topic only"}),
                   ("Secondary (full text)", {"Secondary (full text)"}), ("Excluded or duplicate", {"Exclude", "Already in library"})]:
    sheet(name, H2, [rec(o) for o in sorted((o for o in items if o["decision"] in decs), key=key)], W)
sheet("Search log", ["Date", "Strategy", "Database", "Tool ID", "Query", "Hits reported", "Records kept", "Note"],
      [[l["date"], l["strategy"], l["database"], l["tool_id"], l["query"], l["hits"], l["retrieved"], l["note"]] for l in logs], [11, 12, 18, 7, 70, 10, 10, 50])
wb.save(OUT)
print(Counter(o["decision"] for o in items))
