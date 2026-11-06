# Extraction tables, one per tool

Every workbook follows the format of `niramai_thermalytix_extraction_table.xlsx`:

- **Scoring table**: per-source Final score (yours) and Preliminary score for the 29 STANDING Together items, with totals by formula.
- **Extraction sheet**: Table 1 (descriptive data points) and Table 2 (the 29 items, each with a value, a verbatim quote and the page).
- **Sources to add**: new sources from the 2 Nov literature searches, selected by the Niramai rule (a study of the tool, or a document by its company, with full text). These still need full-text extraction.
- **Duplicates removed**, **Missing full text**, **Read me**.

| Tool | Sources extracted | Still to extract |
|---|---|---|
| Thermalytix (Niramai) | 50 | 0 |
| Smart Scope (Periwinkle) | 10 | 10 |
| CanAssist Breast (OncoStem) | 10 | 30 |
| AVE (NCI–IARC) | 5 | 25 |
| EVA VisualCheck (MobileODT) | 4 | 8 |
| CervAstra (Aindra) | 4 | 0 |
| AIIMS mammography AI | 2 | 0 |
| MammoAssist (Telerad) | 1 | 0 |
| Lord's Mark thermal device | 1 | 0 |
| iBreastExam (UE LifeSciences) | 0 | 21 |
| uPath HER2 (Roche) | 0 | 4 |
| MedXAI | 0 | 0 (CTRI record could not be downloaded) |

"Still to extract" counts Include and Borderline rows. Scripts in `scripts/` rebuild the workbooks from the template.
