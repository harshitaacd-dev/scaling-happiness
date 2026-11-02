# Dissertation literature search: AI breast and cervical cancer screening tools in India

A reproducible search for papers and trial registrations on 13 AI screening tools, run on 2 Nov 2026.
It supports the transparency audit against the 29 STANDING Together recommendations.

## Contents

- `literature_search_results.xlsx`: the results. Start with the **Read me** and **Summary by tool** sheets, then screen the **NEW - Include** sheet (fill in the `YOUR DECISION` column).
- `scripts/`: the search pipeline.
- `data/raw_results.json`: every record returned by every query (before deduplication).
- `data/screened.json`: deduplicated records with suggested decisions.
- `data/existing.json`: index of the existing source library (S01–S62), used to flag sources already held.

## Databases

Europe PMC (titles, abstracts and full text; includes PubMed/MEDLINE and preprints), PubMed, Crossref,
ClinicalTrials.gov, and the WHO ICTRP (which aggregates CTRI). Every query and its hit count is in the
**Search log** sheet.

## Results (2 Nov 2026)

| | Records |
|---|---|
| Unique records after deduplication | 905 |
| Already in library (S01–S62) | 41 |
| New, suggested include | 114 |
| To check | 236 |
| Secondary (tool mentioned only in full text) | 475 |
| Excluded (name clashes, unrelated registry hits) | 39 |

Suggested decisions come from titles and abstracts only and need manual confirmation.

## Re-running

Requires Python 3 with `requests`, `beautifulsoup4` and `openpyxl`.

```bash
python3 scripts/existing.py extraction_table1.xlsx data/existing.json
python3 scripts/search.py data/raw_results.json
python3 scripts/dedupe.py data/raw_results.json data/existing.json data/screened.json
python3 scripts/build_xlsx.py data/screened.json literature_search_results.xlsx data/existing.json
```

Step 1 needs the extraction workbook (not included here); skip it to reuse `data/existing.json`.

## Verification search (2 Nov 2026)

A second search, in `verification/`, checks that the first one missed nothing. It lists **only records not found by
search 1 and not already in the library**.

| Strategy | What it does |
|---|---|
| A. Name variants | Europe PMC with alternative spellings (SmartScope, Smart-Scope, Niramai Health Analytix, Aindra Systems, UE Life Sciences, ...) |
| B. Semantic Scholar / OpenAlex | Not run: both APIs were rate-limited from the cloud session. Re-run `search2.py` from a personal connection or with free API keys |
| C. Citation chasing | Forward citations and reference lists of every known paper (Europe PMC), keeping titles that name a tool |
| D. Topic search | AI + breast/cervical screening + India, not tied to tool names (Europe PMC, ClinicalTrials.gov, WHO ICTRP CTRI records) |

Findings:

- The literature was well covered: only 7 new records name a tool (conference papers, a book chapter, one CTRI trial).
- The trial registries were the gap. A CTRI trial of MobileODT's AI (registered as "Mobile ODT") was missed by search 1.
- Indian AI screening tools registered in CTRI but not on the tool list are in the **Candidate new tools** sheet. PredAID-CERVIA (three 2022 trials) is the strongest.

To re-run: `python3 scripts/search2.py verification/data/raw_results2.json data/screened.json data/existing.json`,
then `compare2.py` and `build_xlsx2.py`.
