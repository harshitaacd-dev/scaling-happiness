# Replication package: Public transparency of the data behind AI cancer screening tools in India

This folder holds the materials needed to check and repeat the audit reported in the research paper: the frozen codebook, the final scores of every source and tool, the analysis data and the scripts. Searches were run between 2 and 7 November 2026; the search registers are in `../literature-search/`.

## What is here

| Folder / file | Contents |
|---|---|
| `codebook/codebook_v1.0.xlsx` | The frozen codebook (version 1.0): 107 elements for the 29 STANDING Together items, with definitions, sources (Laws et al., 2025, Appendix 2, for Part 1; the author's operationalisation for Part 2) and applicability conditions. Reproduced in Appendix A of the paper. |
| `codebook/codebook_v1.0_detection_rules.py` | The search rules used to identify elements in the extracted passages. |
| `data/source_level_scores.csv` | Final score (0/1/2) of each of the 601 sources on each of the 29 items, with tool, source number, type, year, title, authors and location. These are the data behind Appendix B. A tool's score on an item is the highest score in any of its sources. |
| `data/element_coding_final.json.gz` | Element-level coding of all 17,429 item scores: which applicable elements were found and which were missing, the preliminary score and the final (two-step) score. |
| `data/final_results.xlsx` | The results tables of the paper (study flow, tool characteristics, scores, items, training vs evaluation data, group comparisons, source types, validation). |
| `data/tool_level.csv`, `data/source_level.csv`, `data/gap_tests.json` | Inputs and results of the tests of the differences between global and Indian developers (Section 4.4, Table 4.5) and between tools in routine use and other tools (Section 4.4). |
| `data/strategic_sources.csv` | Source-level coding used for the selective-disclosure test (Section 4.5, Figure 4.3). |
| `scripts/` | Scoring and analysis scripts: element identification (`elements.py`, `run_elements.py`), the two-step scoring rule (`apply_hybrid.py`), analysis (`inputs_from_workbooks.py`, `analysis_v3.py`, `robustness_gap.py`, `strategic_disclosure.py`), results tables (`final_results.py`) and Appendix B (`gen_appendix_b.py`). |

## What is not here, and why

- **Full texts** of the sources are not redistributed. Their locations are listed in `data/source_level_scores.csv`.
- **The extraction workbooks with verbatim quotations** are not included, because many quotations come from paywalled papers. Every score above zero rests on such a quotation, checked word for word against the source.

## Running the scripts

The scripts were written for the author's working directory and read the extraction workbooks, which are not included. Paths are given relative to the folder in which the scripts are run (`.`); set them to your own copies of the inputs. The scoring rule and the analyses can be checked directly against the data files above without re-running the extraction.

## Scoring in brief

- 0 = not reported; 1 = some, but not all, applicable elements reported; 2 = all applicable elements reported.
- Whether an item is reported (0 or more) is taken from the verified quotation; whether it is complete (1 or 2) from the count of applicable elements (two-step rule; Sections 3.6 and 3.7 of the paper).
- Measures: items reported (of 29, primary), completeness (share of applicable elements) and total score (of 58, secondary).
