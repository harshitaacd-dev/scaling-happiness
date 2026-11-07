"""One command for the whole full-text routine (steps 4f, 4d, 4, 4b, 4c and optionally 4e).

    python get_fulltexts.py                                   # look in ~/Downloads and ~/Documents for PDFs you already have
    python get_fulltexts.py --folders ~/Downloads/Niramai     # or only in the folders you name
    python get_fulltexts.py --library firefox                 # also run the EUR download helper (you log in yourself)

What it does, in order:
 1. finds PDFs you already have and copies matching ones into manual_pdfs/ (your files are only read, never moved)
 2. looks up free legal copies in Unpaywall (only if UNPAYWALL_EMAIL is set)
 3. reads all new PDFs and texts into the pipeline, removes duplicate copies, rebuilds the missing list
 4. with --library: runs the EUR download helper for what is still missing, then repeats step 3
It finishes with a short summary. Safe to run as often as you like.
"""
import argparse
import json
import os
import subprocess
import sys

from common import DATA, ROOT

PY = sys.executable


def run(step, *args):
    print(f"\n=== {step}", flush=True)
    r = subprocess.run([PY, *args], cwd=ROOT)
    if r.returncode != 0:
        print(f"(this step reported a problem; carrying on)")


def summary():
    d = json.load(open(DATA / "sources.json"))
    live = [r for v in d.values() for r in v if r.get("decision") in ("Include", "Borderline")]
    have = sum(1 for r in live if r.get("text_file"))
    papers_missing = sum(1 for r in live if not r.get("text_file") and r["kind"] == "publication")
    other_missing = sum(1 for r in live if not r.get("text_file") and r["kind"] != "publication")
    dups = sum(1 for v in d.values() for r in v if r.get("decision") == "Duplicate")
    print(f"\n=== SUMMARY\n  full texts ready for extraction: {have}\n  papers still missing: {papers_missing}"
          f"\n  web pages / registrations still missing: {other_missing}\n  duplicate copies set aside: {dups}"
          f"\n  the missing list is in data/missing_fulltexts.csv")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--folders", nargs="*", default=["~/Downloads", "~/Documents"], help="where to look for PDFs you already have")
    ap.add_argument("--library", choices=["firefox", "chrome", "chromium", "safari"], help="also run the EUR download helper with this browser")
    ap.add_argument("--max", type=int, default=40, help="papers per EUR run")
    args = ap.parse_args()

    if args.folders:
        run("1. PDFs you already have", "s4f_import_existing.py", *[os.path.expanduser(f) for f in args.folders])
    if os.environ.get("UNPAYWALL_EMAIL", "").count("@"):
        run("2. Free legal copies (Unpaywall)", "s4d_unpaywall.py")
    else:
        print("\n=== 2. Unpaywall skipped (set it up with:  export UNPAYWALL_EMAIL=your.address)")
    run("3a. Reading new PDFs and texts", "s4_fetch_fulltext.py")
    run("3b. Removing duplicate copies", "s4b_remove_duplicates.py")
    run("3c. Updating the missing list", "s4c_missing_list.py")
    if args.library:
        run("4. EUR library downloads (log in when the browser opens)", "s4e_eur_downloader.py", "--browser", args.library, "--max", str(args.max))
        run("4a. Reading the downloaded PDFs", "s4_fetch_fulltext.py")
        run("4b. Removing duplicate copies", "s4b_remove_duplicates.py")
        run("4c. Updating the missing list", "s4c_missing_list.py")
    summary()
