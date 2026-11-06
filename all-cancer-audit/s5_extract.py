"""Step 5: extract Table 1 (data points) and Table 2 (29 STANDING Together items) from every full text.

One Claude call per source. Every quote is checked against the source text; quotes that cannot be found verbatim
are flagged '[check: quote not found verbatim]'. Results are cached in data/extractions/<source_id>.json, so the
step can be stopped and re-run.  Usage: python s5_extract.py [tool_id ...]
"""
import re
import sys
from concurrent.futures import ThreadPoolExecutor

from common import DATA, ask_json, load, template_labels

EXT = DATA / "extractions"; EXT.mkdir(exist_ok=True)
DPS, ITEMS = template_labels()

FIELD = {"type": "object", "properties": {
    "value": {"type": "string"},
    "quotes": {"type": "array", "items": {"type": "object", "properties": {"text": {"type": "string"}, "page": {"type": "string"}},
                                          "required": ["text", "page"], "additionalProperties": False}}},
    "required": ["value", "quotes"], "additionalProperties": False}
SCORED = {"type": "object", "properties": {**FIELD["properties"], "score": {"type": "integer", "enum": [0, 1, 2]}},
          "required": ["value", "quotes", "score"], "additionalProperties": False}
HEADER = ["company", "ai_tool", "source_type", "title", "authors", "year", "registration_ids", "extraction_notes"]
SCHEMA = {"type": "object", "properties": {
    **{h: {"type": "string"} for h in HEADER},
    **{f"dp{i + 1:02d}": FIELD for i in range(len(DPS))},
    **{f"it{i + 1:02d}": SCORED for i in range(len(ITEMS))}},
    "required": HEADER + [f"dp{i + 1:02d}" for i in range(len(DPS))] + [f"it{i + 1:02d}" for i in range(len(ITEMS))],
    "additionalProperties": False}

SYSTEM = f"""You extract evidence for a transparency audit of AI cancer tools against the STANDING Together recommendations
(29 items on the documentation and use of health datasets). Work only from the source text given; use no outside knowledge.

Header fields: company and ai_tool as named in the source (write e.g. "Breast cancer risk model (Thermalytix not named in source)"
when the source does not name the product); source_type (paper, preprint, conference abstract, conference paper, trial registration,
patent, web page, book chapter, case report, magazine feature, ...); year; authors (up to 6, then "et al."; "Not reported" for registries
and web pages, adding the contact or publisher in brackets); registration_ids: every trial registration number in the text (CTRI/..., NCT...),
separated by "; ", or "None"; extraction_notes: one or two sentences on what was extracted and anything unusual (scope, OCR, missing parts).

For each data point and each item: value = a short factual summary of what the source reports, or exactly "Not reported";
quotes = the supporting passages copied VERBATIM from the text (character for character, no paraphrase, no ellipses inside a quote;
use several short quotes rather than one long one), each with its page: the number from the nearest preceding '=== PAGE n ===' marker,
or "web page, no page numbers" / "no page numbers" when the text has no page markers. When the value is "Not reported", quotes is empty.
Score key for the 29 items: 0 = no information, 1 = partial information, 2 = complete information. Score what is disclosed about the
data used to develop or evaluate the tool, as the recommendation asks.
If the text holds several abstracts (a journal supplement or abstract book), extract only the abstract(s) about the tool named below.

DATA POINTS (Table 1, descriptive):
""" + "\n".join(f"dp{i + 1:02d}: {d}" for i, d in enumerate(DPS)) + "\n\nSTANDING TOGETHER ITEMS (Table 2, scored):\n" + \
    "\n".join(f"it{i + 1:02d}: {s.split(' — ')[0]} | {lab}" for i, (s, lab) in enumerate(ITEMS))


def squash(s):
    s = s.replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'").replace("–", "-").replace("—", "-")
    s = re.sub(r"-\s*\n\s*", "", s)  # words hyphenated across lines
    return re.sub(r"\s+", " ", s).strip().lower()


def render(field, text_sq):
    out = []
    for q in field["quotes"]:
        page = q["page"].strip()
        tag = f"({page})" if not re.fullmatch(r"\d+(-\d+)?", page) else f"(p. {page})"
        flag = "" if squash(q["text"])[:200] in text_sq else " [check: quote not found verbatim]"
        out.append(f"“{q['text'].strip()}” {tag}{flag}")
    return "\n\n".join(out) or None


def extract(tool_name, src):
    path = EXT / f"{src['source_id']}.json"
    if path.exists():
        return "cached"
    text = (DATA / "texts" / src["text_file"]).read_text()
    if len(text) > 2_500_000:
        return "skipped: text too long for one request; split the PDF and add the parts to manual_pdfs/"
    prompt = f"TOOL BEING AUDITED: {tool_name}\nSOURCE: {src['title']}\n\n<source_text>\n{text}\n</source_text>"
    out = ask_json(SYSTEM, prompt, SCHEMA, effort="high")
    sq = squash(text)
    out["_rendered"] = {
        "dp": [[out[f"dp{i + 1:02d}"]["value"], render(out[f"dp{i + 1:02d}"], sq)] for i in range(len(DPS))],
        "items": [[out[f"it{i + 1:02d}"]["value"], render(out[f"it{i + 1:02d}"], sq), out[f"it{i + 1:02d}"]["score"]] for i in range(len(ITEMS))],
    }
    out["_unverified_quotes"] = sum(str(c).count("[check:") for row in out["_rendered"]["dp"] + out["_rendered"]["items"] for c in row)
    path.write_text(__import__("json").dumps(out, indent=1, ensure_ascii=False))
    return f"done ({out['_unverified_quotes']} quotes to check)"


def _safe(name, s):
    try:
        return extract(name, s)
    except Exception as e:  # keep going; failed sources are retried on the next run
        return f"ERROR {type(e).__name__}: {e}"


if __name__ == "__main__":
    import csv
    only = set(sys.argv[1:])
    names = {t["tool_id"]: t["tool_name"] for t in csv.DictReader(open(DATA / "corpus.csv", encoding="utf-8-sig"))}
    sources = load("sources.json")
    jobs = [(names.get(tid, tid), s) for tid, recs in sources.items() if not only or tid in only for s in recs if s.get("text_file") and s.get("decision") in ("Include", "Borderline")]
    print(f"{len(jobs)} sources to extract", flush=True)
    with ThreadPoolExecutor(max_workers=4) as pool:  # a few requests at a time
        for (name, s), res in zip(jobs, pool.map(lambda j: _safe(*j), jobs)):
            print(f"{s['source_id']:45s} {res}", flush=True)
