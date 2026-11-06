"""Assemble per-tool spec: library sources, duplicates, same-study links, missing files, new sources to add."""
import json, re, sys
sys.path.insert(0, sys.argv[1])
from selection import SEL, CANASSIST_EXCLUDE
lib = json.load(open(sys.argv[2])); s1 = json.load(open(sys.argv[3]))["items"]; s2 = json.load(open(sys.argv[4]))["items"]; OUT = sys.argv[5]

TOOLS = [  # label, sheet name, file, old sheet, search tool id
 ("Smart Scope (Periwinkle)", "Periwinkle (Smart Scope)", "periwinkle_smartscope_extraction_table.xlsx", "Smart Scope (Periwinkle)", "T02"),
 ("CanAssist Breast (OncoStem)", "OncoStem (CanAssist Breast)", "oncostem_canassist_extraction_table.xlsx", "CanAssist Breast (OncoStem)", "T03"),
 ("AVE (NCI - IARC)", "NCI-IARC (AVE)", "nci_ave_extraction_table.xlsx", "AVE (NCI - IARC)", "T04"),
 ("EVA VisualCheck (MobileODT)", "MobileODT (EVA VisualCheck)", "mobileodt_eva_extraction_table.xlsx", "EVA VisualCheck (MobileODT)", "T05"),
 ("CervAstra (Aindra)", "Aindra (CervAstra)", "aindra_cervastra_extraction_table.xlsx", "CervAstra (Aindra)", "T06"),
 ("AIIMS New Delhi", "AIIMS (mammography AI)", "aiims_mammography_extraction_table.xlsx", "AIIMS New Delhi", "T07"),
 ("MammoAssist (Telerad Tech)", "Telerad (MammoAssist)", "telerad_mammoassist_extraction_table.xlsx", "MammoAssist (Telerad Tech)", "T08"),
 ("Lord's Mark Industries", "Lord's Mark (thermal device)", "lordsmark_extraction_table.xlsx", "Lord's Mark Industries", "T09"),
 ("iBreastExam (UE LifeSciences)", "UE LifeSciences (iBreastExam)", "ue_ibreastexam_extraction_table.xlsx", None, "T10"),
 ("uPath HER2 (Roche)", "Roche (uPath HER2)", "roche_upath_extraction_table.xlsx", None, "T12"),
 ("MedXAI cervical AI", "MedXAI (cervical AI)", "medxai_extraction_table.xlsx", None, "T13"),
]
DUPS = {"S21": "S01", "S19": "S04"}
MISSING_TOOL = {"S37": "T02", "S30": "T07", "S39": "T13", "S35": None, "S27": None, "S57": None}

def norm_items(tid):
    out = []
    for o in s1:
        if tid in o["tool_ids"] and not o["existing"]:
            ident = o["trial_id"] or (f'doi:{o["doi"]}' if o["doi"] else (f'PMID:{o["pmid"]}' if o["pmid"] else ""))
            out.append(dict(kind=o["kind"], year=o["year"], title=o["title"], authors=o["authors"], venue=o["venue"], id=ident,
                            oa=o["open_access"], link=o["link"], abstract=o["abstract"], suggestion=o["suggestion"]))
    for o in s2:
        if o["decision"] == "Include":
            out.append(dict(kind=o["kind"], year=o["year"], title=o["title"], authors=o["authors"], venue=o["venue"], id=o["ident"],
                            oa=o["open_access"], link=o["link"], abstract=o["abstract"], suggestion="Include", tool=o["tool"]))
    return out

spec = []
for label, sheet, fname, oldsheet, tid in TOOLS:
    # library sources of this tool
    srcs = sorted(s for s, v in lib.items() if v["tool"] == oldsheet)
    keep = [s for s in srcs if s not in DUPS]
    regs = {i: s for s in keep if lib[s]["type"] == "trial_registration" for i in lib[s]["ids"] if i.startswith(("CTRI", "NCT"))}
    same = {}
    for s in keep:
        if lib[s]["type"] == "trial_registration": continue
        for i in lib[s]["ids"]:
            if i in regs:
                same.setdefault(s, []).append(f"{regs[i]} (registration {i})"); same.setdefault(regs[i], []).append(f"{s} (paper)")
    for a, b in DUPS.items():
        if a in srcs:
            pass
    same = {k: "; ".join(sorted(set(v))) for k, v in same.items()}
    dups = [[f"{a} ({lib[a]['title']})", f"{b}: {lib[b]['title']}", "Same publication as a source already in the workbook"] for a, b in DUPS.items() if a in srcs]
    missing = [[f"{s}: {lib[s]['title']}", "Download failed or only an abstract page was saved; no full text in the library."] for s, t in MISSING_TOOL.items() if t == tid]
    # new sources
    cands = norm_items(tid)
    sel = SEL.get(label)
    to_add, seen = [], set()
    if sel == "ALL_INCLUDE":
        for c in cands:
            if c["suggestion"] != "Include" or c["id"] in seen: continue
            if c.get("tool") and "CanAssist" not in c["tool"]: continue
            ex = next((v for k, v in CANASSIST_EXCLUDE.items() if k in c["id"] or k in c["title"]), None)
            if re.search(r"special needs|older adults", c["title"], re.I): continue
            seen.add(c["id"]); to_add.append(dict(c, dec="Exclude" if ex else "Include", note=ex or "Study of the tool or by OncoStem"))
    elif sel:
        for key, dec, note in sel:
            hit = next((c for c in cands if key.lower() in (c["id"] + " " + c["title"]).lower()), None)
            if hit is None:
                hit = next((dict(kind=o["kind"], year=o["year"], title=o["title"], authors=o["authors"], venue=o["venue"], id=o["ident"], oa=o["open_access"], link=o["link"], abstract=o["abstract"])
                            for o in s2 if key.lower() in (o["ident"] + " " + o["title"]).lower()), None)
            if hit is None: print("NOT FOUND", label, key); continue
            if hit["id"] in seen and hit["id"]: continue
            seen.add(hit["id"]); to_add.append(dict(hit, dec=dec, note=note or "Study of the tool"))
    to_add.sort(key=lambda a: ({"Include": 0, "Borderline": 1, "Exclude": 2}[a["dec"]], a["kind"], str(a["year"])))
    n_inc = sum(a["dec"] == "Include" for a in to_add); n_b = sum(a["dec"] == "Borderline" for a in to_add)
    readme = [
        f"{label} sources only. No. 1–{len(keep)} are this tool's sources from the original extraction table (S-numbers {', '.join(keep) or 'none'}), extracted from full text." if keep else f"{label}: no sources from the original extraction table. All sources are in 'Sources to add' and are pending full-text extraction.",
        "Each extraction sheet has two tables. Table 1 — Data points (sample size, country/state, setting, design, cancer type, AI modality, reference standard, sensitivity, specificity, demographics): Value and verbatim supporting quote (page); descriptive, not scored. Table 2 — the 29 STANDING Together items: Value, verbatim supporting quote (page), Final score (grey, left empty for you) and Preliminary score (0/1/2). Each source is a column block headed by its S. No. and source details.",
        "The 'Scoring table' sheet (first tab) holds the STANDING Together scores only: for each source, the Final score (linked to the grey Final score cells of Table 2, so enter scores there) and the Preliminary score. Totals for Part 1 (max 36), Part 2 (max 22) and the overall STANDING Together total (max 58), the % of maximum and the number of items with a final score are calculated with formulas. Columns C–H give row totals for every STANDING Together item summed over all sources.",
        "Score key: 0 = no information, 1 = partial information, 2 = complete information. Preliminary scores are Claude's; the Final score is yours.",
        "'Not reported' means the item was not found in the source text. No outside knowledge was used.",
        "Page numbers refer to the PDF page (1 = first page of the PDF file). Trial registrations and web pages have no page numbers and are marked 'web page, no page numbers'.",
        "Sources are identified by S. No. only. 'Same study as' links separate documents that report the same study (worked out from the trial registration numbers each source cites); they are kept as separate sources, and only copies of the same document were removed as duplicates.",
        f"'Sources to add': new sources found by the literature searches of 2 Nov 2026 (see the scaling-happiness repository), selected with the same rule used for Niramai: a study of the tool or a document by its company, with full text. Include: {n_inc}; Borderline (check before extracting): {n_b}; Exclude (kept for the record): {len(to_add) - n_inc - n_b}. These are not yet extracted.",
        f"Sources completed: {len(keep)}",
    ]
    spec.append(dict(label=label, sheet=sheet, file=fname, old_sheet=oldsheet if keep else None, drop=list(DUPS), same=same, dups=dups, missing=missing, to_add=to_add, readme=readme))
    print(f"{label:32s} library={len(keep):2d} add: include={n_inc:2d} borderline={n_b} exclude={len(to_add)-n_inc-n_b}")
json.dump(spec, open(OUT, "w"), indent=1)
