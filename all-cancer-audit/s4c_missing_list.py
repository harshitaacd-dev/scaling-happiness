"""Step 4c: list the sources that still need a full text, so you can download them by hand.

Writes data/missing_fulltexts.csv and creates the manual_pdfs/<tool_id>/ folders.
For each row: save the PDF into the 'save_in_folder' folder under the name in 'save_as', then re-run
step 4 (python s4_fetch_fulltext.py) and step 4b. Files named this way are matched to their source exactly.
Web pages that would not download can be saved as PDF from the browser (File > Print > Save as PDF).
Also lists papers whose saved text looks like an abstract page only (short text), so you can replace them.
"""
import csv
from urllib.parse import quote

from common import DATA, ROOT, load, looks_like_gate, save

PROXY = "https://eur.idm.oclc.org/login?url="  # Erasmus University library proxy
PRIORITY = {"publication": 1, "trial registration": 2, "web page": 3}

if __name__ == "__main__":
    sources = load("sources.json")
    rows, gate_fixed = [], 0
    for tid, recs in sources.items():
        for r in recs:
            if r.get("decision") not in ("Include", "Borderline") or not r.get("source_id"):
                continue
            reason = None
            if r.get("text_file") and looks_like_gate((DATA / "texts" / r["text_file"]).read_text(), r["kind"]):
                (DATA / "texts" / r["text_file"]).unlink()
                r.pop("text_file"); r.pop("manual_pdf", None)
                r["fulltext_status"] = "missing: saved text was a login/paywall page"
                gate_fixed += 1
            if not r.get("text_file"):
                reason = "no full text" if "login/paywall" not in r.get("fulltext_status", "") else "saved text was a login or paywall page"
            elif r["kind"] == "publication" and not r.get("manual_pdf"):
                size = (DATA / "texts" / r["text_file"]).stat().st_size
                if size < 8000:
                    reason = f"only {size // 1000} KB of text saved: probably the abstract page; replace with the PDF"
            if not reason:
                continue
            doi_link = f"https://doi.org/{r['doi']}" if r.get("doi") else ""
            target = doi_link or r.get("url", "")
            rows.append({
                "priority": PRIORITY.get(r["kind"], 3),
                "tool_id": tid,
                "kind": r["kind"],
                "year": r.get("year", ""),
                "title": r["title"],
                "authors": r.get("authors", "")[:120],
                "journal_or_site": r.get("venue", ""),
                "why_listed": reason,
                "doi_link": doi_link,
                "library_link (EUR proxy)": (PROXY + quote(target, safe="")) if r["kind"] == "publication" and target else "",
                "original_link": r.get("url", ""),
                "save_in_folder": f"manual_pdfs/{tid}",
                "save_as": f"{r['source_id']}.pdf",
                "done (y/n)": "",
            })
            (ROOT / "manual_pdfs" / tid).mkdir(parents=True, exist_ok=True)
    save("sources.json", sources)
    if gate_fixed:
        print(f"{gate_fixed} saved texts were login/paywall pages: removed and put back on the list")
    rows.sort(key=lambda x: (x["priority"], x["tool_id"], str(x["year"])))
    out = DATA / "missing_fulltexts.csv"
    with open(out, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["priority"])
        w.writeheader(); w.writerows(rows)
    from collections import Counter
    print(f"{len(rows)} sources listed in {out.relative_to(ROOT)}")
    for k, v in sorted(Counter((x["priority"], x["kind"]) for x in rows).items()):
        print(f"  priority {k[0]} ({k[1]}): {v}")
    print("Folders created under manual_pdfs/. Save each PDF with the name in 'save_as', then re-run steps 4 and 4b.")
