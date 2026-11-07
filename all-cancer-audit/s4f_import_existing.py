"""Step 4f: use PDFs you already have (e.g. your Niramai folder or the earlier source library) instead of downloading them again.

Give one or more folders. Every PDF in them (including subfolders) is read and matched to a source that still needs a
full text, by DOI or by title. Matches are COPIED (your originals are untouched) into manual_pdfs/<tool_id>/<source_id>.pdf,
which is where step 4 picks them up.

Usage:   python s4f_import_existing.py ~/Downloads/Niramai ~/Documents/source-library-kit
Then:    python s4_fetch_fulltext.py   and   python s4b_remove_duplicates.py   and   python s4c_missing_list.py
Use --dry-run first to see what would be matched without copying anything.
"""
import argparse
import difflib
import re
import shutil
from pathlib import Path

from pypdf import PdfReader

from common import DATA, ROOT, load, looks_like_gate, norm


def first_pages_text(path, pages=2):
    try:
        reader = PdfReader(str(path))
        return " ".join((p.extract_text() or "") for p in reader.pages[:pages])
    except Exception:
        return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("folders", nargs="+")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    sources = load("sources.json")
    wanted = []  # sources still needing a full text (or only an abstract page saved)
    for tid, recs in sources.items():
        for r in recs:
            if r.get("decision") not in ("Include", "Borderline") or r["kind"] != "publication" or not r.get("source_id"):
                continue
            short = r.get("text_file") and not r.get("manual_pdf") and (DATA / "texts" / r["text_file"]).stat().st_size < 8000
            if not r.get("text_file") or short:
                if not (ROOT / "manual_pdfs" / tid / f"{r['source_id']}.pdf").exists():
                    wanted.append((tid, r, norm(r["title"]), (r.get("doi") or "").lower()))
    print(f"{len(wanted)} papers still need a full text")

    skip = (ROOT.resolve(),)
    pdfs = [p for f in args.folders for p in Path(f).expanduser().rglob("*.pdf")
            if not any(str(p.resolve()).startswith(str(x)) for x in skip) and "/." not in str(p)]
    print(f"{len(pdfs)} PDFs found in {', '.join(args.folders)}")
    matched, used = 0, set()
    for pdf in pdfs:
        text = first_pages_text(pdf)
        if not text or looks_like_gate(text, "publication"):
            continue
        low = text.lower(); head = norm(text[:4000]); name = norm(pdf.stem)
        best = None
        for tid, r, title, doi in wanted:
            if r["source_id"] in used:
                continue
            if doi and doi in low:
                best = (tid, r, "DOI"); break
            if len(title) > 25 and (title[:60] in head or title[:60] in name):
                best = (tid, r, "title"); break
            words = [w for w in title.split() if len(w) > 3]
            if len(words) >= 6:
                head_words = set(head.split())
                cover = sum(w in head_words for w in words) / len(words)
                if cover >= 0.85:
                    best = (tid, r, f"title words ({cover:.0%})"); break
            if len(title) > 25:
                ratio = difflib.SequenceMatcher(None, title[:120], name[:120]).ratio()
                if ratio > 0.9:
                    best = (tid, r, f"file name ({ratio:.2f})"); break
        if best is None:
            continue
        tid, r, how = best
        dest = ROOT / "manual_pdfs" / tid / f"{r['source_id']}.pdf"
        print(f"  {'would copy' if args.dry_run else 'copied'} [{how}] {pdf.name[:50]}  ->  {dest.relative_to(ROOT)}")
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pdf, dest)
        used.add(r["source_id"]); matched += 1
    print(f"\n{matched} PDFs {'would be' if args.dry_run else 'were'} matched.")
    if matched and not args.dry_run:
        print("Next: python s4_fetch_fulltext.py, then python s4b_remove_duplicates.py, then python s4c_missing_list.py")


if __name__ == "__main__":
    main()
