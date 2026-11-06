# Prompt to paste into a new Claude Code session

Start a new Claude Code session with the `harshitaacd-dev/scaling-happiness` repository attached, then paste the text below.

---

I'm auditing how publicly transparent AI cancer tools in India are about their data, and comparing tools for women-specific
cancers (breast, cervical, ovarian, uterine) with tools for other cancers. The pipeline is in `all-cancer-audit/`; read its
README.md first.

Please:

1. Install the requirements and check that an Anthropic API key or `ant` login is available. If none is, stop and tell me.
2. Run step 1 (`python s1_discover_tools.py`) and step 2 (`python s2_build_corpus.py`).
3. Show me `data/corpus.csv` as a table grouped by sex group: tool, company, cancer, purpose, status in India, suggested include and reason.
   **Wait for me to confirm or change the include decisions before going on.**
4. Run step 3 and step 4. Then tell me, per tool, how many sources were included and which have no open-access full text,
   so I can download those PDFs into `manual_pdfs/<tool_id>/`.
5. Run step 5 on one tool first and tell me the cost and the number of unverified quotes. Wait for my go-ahead, then run the rest.
6. Run step 6, commit the `output/` workbooks and `data/` (except `data/texts/`) to a new folder in the repository, and push.

Rules: do not change the inclusion rules or the extraction prompt without asking me. If a step fails, show me the error and
what you propose to change. Keep your messages short.
