# All-cancer AI tool audit (India)

Research question: *How publicly transparent are AI cancer tools deployed in India about their data, and is transparency
lower for tools for women-specific cancers?*

This pipeline finds AI cancer screening tools used in India, builds the corpus, collects every public source on each tool,
extracts the 29 STANDING Together items with verbatim quotes, and writes one workbook per tool in the same format as
`../extraction-tables/niramai_thermalytix_extraction_table.xlsx`, plus a comparison by sex group.

## Setup

```bash
cd all-cancer-audit
```

```bash
pip install -r requirements.txt
```

```bash
export ANTHROPIC_API_KEY=your-key
```

The template workbook must stay at `../extraction-tables/niramai_thermalytix_extraction_table.xlsx`.
All model calls use Claude Opus 5.5 with a server-side fallback if a request is declined. To use a cheaper model, set
`AUDIT_MODEL` (e.g. `export AUDIT_MODEL=claude-sonnet-5-5`); say so in your methods if you do.

## Steps

| Step | Command | What it does | Output |
|---|---|---|---|
| 1 | `python s1_discover_tools.py` | Claude web research for 14 cancer types + CTRI searches (AI/deep learning/machine learning × cancer) | `data/discovery_web.json`, `data/discovery_ctri.json` |
| 2 | `python s2_build_corpus.py` | Merges everything into one classified, deduplicated tool list (sex group, purpose, status, search terms) | `data/corpus.csv` |
| **review** | open `data/corpus.csv` | **Set `include` to yes/no for every tool.** Check sex group and purpose. Edit search terms if needed | |
| 3 | `python s3_find_sources.py` | Europe PMC, PubMed, Crossref, ClinicalTrials.gov, WHO ICTRP + web search for company pages; screens with the Niramai rule | `data/sources.json`, `data/search_log.json` |
| **4 (all in one)** | `python get_fulltexts.py` (add `--library firefox` to also use the EUR helper) | **Recommended.** Runs 4f, 4d, 4, 4b and 4c (and 4e) in the right order and prints a summary. Steps 4–4f below can also be run one by one | `data/texts/`, `data/missing_fulltexts.csv` |
| 4 | `python s4_fetch_fulltext.py` | Downloads open-access full texts, trial records and web pages | `data/texts/`, updates `sources.json` |
| 4b | `python s4b_remove_duplicates.py` | Removes republished copies of the same article (keeps the original) and non-English versions | updates `sources.json` |
| 4c | `python s4c_missing_list.py` | Lists every source still without full text (and abstract-only pages), with library links and the exact file name to save | `data/missing_fulltexts.csv` |
| 4d | `python s4d_unpaywall.py` | Finds free legal copies of missing papers via Unpaywall (set `UNPAYWALL_EMAIL` first) | updates `sources.json` |
| 4e | `python s4e_eur_downloader.py` | Opens a browser on your computer; **you** log in to the EUR library; it saves the missing PDFs slowly (20–40 s apart, max 40 per run) and stops at any block/captcha page. Needs `pip install playwright` and `python -m playwright install chromium` once | `manual_pdfs/`, `data/eur_download_log.csv` |
| 4f | `python s4f_import_existing.py ~/Downloads/Niramai` | Copies PDFs you already have (matched by DOI or title) into place, so they are not downloaded again | `manual_pdfs/` |
| **paywalled** | put PDFs in `manual_pdfs/<tool_id>/` | Download them with your library proxy, then re-run step 4 and step 4b | |
| 5 | `python s5_extract.py` | Extracts Table 1 and the 29 items for every source; checks every quote against the text | `data/extractions/` |
| 6 | `python s6_build_workbooks.py` | One workbook per tool + `comparison_by_sex_group.xlsx` | `output/` |

**Where are we?** `python status.py` shows, per tool and in total, what is found, downloaded, missing, extracted and built, and what to do next.

Every step can be stopped and re-run: finished work is cached and skipped. `python s5_extract.py <tool_id>` extracts one tool only.

## The inclusion rules

- **Tools (step 2):** uses AI/ML; a named product or programme; screening, early detection or diagnosis of cancer; used, trialled,
  licensed or approved in India. After-diagnosis tools (like CanAssist) are listed but suggested as `no`; you decide.
- **Sources (step 3), the Niramai rule:** a study of the tool or a document by its company, with full text. Excluded: third-party reviews,
  commentaries and modelling papers that only mention the tool; studies using the company's hardware without the AI; different products
  with similar names.
- **Sex groups:** women-specific = breast, cervical, ovarian, uterine; men-specific = prostate, testicular; all = the rest.
  Breast cancer also occurs in men, but rarely; say how you classify it in the methods.

## Checking the output

- Quotes marked `[check: quote not found verbatim]` could not be matched to the source text by script. Check them by hand.
- Preliminary scores are Claude's. Enter your Final scores in the grey cells of each workbook, then re-run step 6 to refresh the
  comparison (it uses Final scores where entered). `python s6_build_workbooks.py --rebuild` rebuilds the workbooks and **overwrites**
  any Final scores you typed, so only use it before scoring.
- Tool-level score per item = the highest score that item reaches in any public source of the tool.

## Cost

Rough guide: steps 1-3 cost tens of dollars for ~50 tools. Step 5 is the main cost, roughly $0.30-0.60 per source at Claude Opus 5.5
prices; run one tool first (`python s5_extract.py <tool_id>`) and check the spend in the Anthropic Console before running everything.

## Limitations to report

- Web discovery depends on what is indexed online; tools with no web presence are missed (that absence is itself a finding).
- Semantic Scholar and OpenAlex are not queried; Europe PMC full-text search covers much of the same ground.
- Paywalled papers are only included if you add the PDFs.
- Groups are small; compare descriptively. Differences may also reflect company size, regulation or number of sources.
