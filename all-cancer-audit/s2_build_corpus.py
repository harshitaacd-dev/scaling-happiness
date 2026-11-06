"""Step 2: turn the discovery notes into one deduplicated, classified tool list (the corpus).

Output: data/corpus.csv  <- REVIEW THIS FILE. Set the `include` column to yes/no before step 3.
The tools already audited (Niramai and the breast/cervical set) are added as seeds so they are not lost.
"""
import csv

from common import DATA, ask_json, load, slug

SEED = [  # tools already in the breast/cervical audit
    ("Thermalytix", "Niramai Health Analytix", "breast"), ("Smart Scope CX", "Periwinkle Technologies", "cervical"),
    ("CanAssist Breast", "OncoStem Diagnostics", "breast"), ("Automated Visual Evaluation (AVE)", "NCI / IARC", "cervical"),
    ("EVA VisualCheck", "MobileODT", "cervical"), ("CervAstra", "Aindra Systems", "cervical"),
    ("AIIMS mammography AI", "AIIMS New Delhi / BPL Medical", "breast"), ("MammoAssist", "Telerad Tech", "breast"),
    ("AI wearable thermal breast device", "Lord's Mark Industries", "breast"), ("iBreastExam", "UE LifeSciences", "breast"),
    ("uPath HER2", "Roche", "breast"), ("MedXAI cervical AI", "MedXAI", "cervical"),
    ("MedCognetics breast AI", "MedCognetics", "breast"), ("GrivaVision colposcope", "GrivaVision", "cervical"),
    ("PredAID-CERVIA", "BlockAppsAI", "cervical"),
]

TOOL = {
    "type": "object",
    "properties": {
        "tool_name": {"type": "string"},
        "company": {"type": "string"},
        "company_country": {"type": "string"},
        "cancer_types": {"type": "string"},
        "sex_group": {"type": "string", "enum": ["women-specific", "men-specific", "all"]},
        "purpose": {"type": "string", "enum": ["screening / early detection", "diagnosis", "after diagnosis (grading, prognosis, treatment)"]},
        "modality": {"type": "string"},
        "india_evidence": {"type": "string"},
        "status_in_india": {"type": "string", "enum": ["deployed", "trialled or piloted", "licensed or approved only", "unclear"]},
        "regulatory": {"type": "string"},
        "source_urls": {"type": "string"},
        "search_terms": {"type": "array", "items": {"type": "string"}},
        "name_regex": {"type": "string"},
        "suggested_include": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["tool_name", "company", "company_country", "cancer_types", "sex_group", "purpose", "modality", "india_evidence",
                 "status_in_india", "regulatory", "source_urls", "search_terms", "name_regex", "suggested_include", "reason"],
    "additionalProperties": False,
}
SCHEMA = {"type": "object", "properties": {"tools": {"type": "array", "items": TOOL}}, "required": ["tools"], "additionalProperties": False}

SYSTEM = """You build the corpus for a transparency audit of AI cancer tools in India.
Merge the research notes and registry records into one deduplicated list of tools (one row per product; merge aliases).
Inclusion rule (suggested_include = true): uses AI/ML; a named product or programme; screening, early detection or diagnosis of cancer
(after-diagnosis tools are listed but suggested_include = false unless the notes show they are central to screening);
used, trialled, licensed or approved in India. Exclude unnamed academic models and tools only in development.
sex_group: women-specific for breast, cervical, ovarian and uterine cancers; men-specific for prostate and testicular; otherwise all.
search_terms: 2-4 exact phrases for literature databases (product name, company name, known aliases), quoted where needed.
name_regex: a case-insensitive Python regex matching the product or company name in a title or abstract.
Keep every seed tool. Do not invent tools or evidence: use only what the notes and records contain."""

if __name__ == "__main__":
    web = load("discovery_web.json", {}); ctri = load("discovery_ctri.json", {})
    trials = {t["trial_id"]: t["title"] for v in ctri.values() for t in v}
    text = "SEED TOOLS (already in the audit; keep all):\n" + "\n".join(f"- {a} | {b} | {c}" for a, b, c in SEED)
    text += "\n\nWEB RESEARCH NOTES BY CANCER TYPE:\n" + "\n\n".join(f"### {k} ({v['sex_group']})\n{v['notes']}" for k, v in web.items())
    text += "\n\nINDIAN TRIAL REGISTRATIONS (CTRI) FOUND BY AI + CANCER SEARCHES:\n" + "\n".join(f"- {k}: {v}" for k, v in sorted(trials.items()))
    out = ask_json(SYSTEM, text, SCHEMA, effort="high")["tools"]
    seen, rows = set(), []
    for t in out:
        tid = slug(f"{t['company']} {t['tool_name']}")
        if tid in seen:
            continue
        seen.add(tid)
        rows.append(dict(tool_id=tid, include="yes" if t["suggested_include"] else "no", **{k: ("; ".join(v) if isinstance(v, list) else v) for k, v in t.items()}))
    with open(DATA / "corpus.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print(f"{len(rows)} tools, {sum(r['include'] == 'yes' for r in rows)} suggested for inclusion -> data/corpus.csv (review it)")
