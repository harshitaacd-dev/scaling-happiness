"""Step 4b: remove copies of the same document before extraction.

News sites often republish a company press release word for word, so one press release can appear as many 'sources'.
Within each tool, sources whose downloaded texts largely overlap (shared 8-word sequences) are treated as copies of one
document: the copy from the company's own site, or else the longest text, is kept; the others are marked
decision = "Duplicate" with duplicate_of = the kept source. Non-English versions (e.g. Hindi/Hinglish pages) are marked
"Exclude" under the English-only criterion. Duplicates are listed in each workbook's 'Duplicates removed' sheet.
Run after step 4 (and again after adding manual PDFs). Safe to re-run.
"""
import re
from urllib.parse import urlparse

from common import DATA, load, save

THRESHOLD = 0.5  # share of the shorter text's 8-word sequences found in the other text


def shingles(text, n=8):
    words = re.findall(r"[a-z0-9]+", text.lower())
    return {" ".join(words[i:i + n]) for i in range(max(0, len(words) - n + 1))}


def overlap(a, b):
    if not a or not b:
        return 0.0
    return len(a & b) / min(len(a), len(b))


NON_ENGLISH = re.compile(r"hinglish|/hindi/|/hi/|/mr/|/ta/|/te/|/bn/|/gu/|/kn/|/ml/", re.I)

if __name__ == "__main__":
    import csv
    corpus = {t["tool_id"]: t for t in csv.DictReader(open(DATA / "corpus.csv", encoding="utf-8-sig"))}
    sources = load("sources.json")
    total = 0
    for tid, recs in sources.items():
        company_words = [w for w in re.findall(r"[a-z]{4,}", corpus.get(tid, {}).get("company", "").lower())]
        live = []
        for r in recs:
            if r.get("decision") == "Duplicate":
                r["decision"] = r.pop("decision_before_dedupe", "Include")  # recompute from scratch on re-runs
            if r.get("decision") not in ("Include", "Borderline") or not r.get("text_file"):
                continue
            if NON_ENGLISH.search(r.get("url", "")):
                r["decision"], r["reason"] = "Exclude", "Not in English (language criterion)"
                continue
            text = (DATA / "texts" / r["text_file"]).read_text()
            host = urlparse(r.get("url", "")).netloc.lower()
            own_site = any(w in host for w in company_words)
            live.append([r, shingles(text), len(text), own_site, host])
        # drop text repeated across pages of the SAME website (menus, footers, templates) before comparing;
        # text repeated across DIFFERENT websites is kept, because that is what a republished press release looks like
        from collections import Counter, defaultdict
        by_host = defaultdict(list)
        for x in live:
            by_host[x[4]].append(x)
        for host_docs in by_host.values():
            if len(host_docs) < 2:
                continue
            df = Counter(sh for x in host_docs for sh in x[1])
            common = {sh for sh, c in df.items() if c >= 2}
            for x in host_docs:
                x[1] = x[1] - common
        # keep originals first: papers and registrations, then the company's own site, then the longest text
        live.sort(key=lambda x: (x[0]["kind"] == "web page", not x[3], -x[2]))
        kept = []
        for r, sh, _, _, _ in live:
            # different trial registrations are different documents, whatever their shared template text
            match = None if r["kind"] == "trial registration" else next(
                (k for k in kept if k[0]["kind"] != "trial registration" and overlap(sh, k[1]) >= THRESHOLD), None)
            if match is None:
                kept.append((r, sh))
            else:
                r["decision_before_dedupe"] = r["decision"]
                r["decision"], r["duplicate_of"] = "Duplicate", match[0]["source_id"]
                r["reason"] = f"Same text as {match[0]['title'][:80]} ({match[0].get('url', '')})"
                total += 1
        n_dup = sum(r.get("decision") == "Duplicate" for r in recs)
        if n_dup:
            print(f"{tid[:45]:45s} kept {len(kept):3d}, duplicates {n_dup:3d}")
    save("sources.json", sources)
    print(f"{total} duplicate copies marked; they will be skipped by step 5")
