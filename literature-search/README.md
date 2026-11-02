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
