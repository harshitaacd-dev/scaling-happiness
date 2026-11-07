"""Step 4d: find free, legal copies of missing papers through Unpaywall.

Unpaywall (unpaywall.org) lists legal open-access copies: author repositories, preprints, publisher OA pages.
It asks for your email address with each request. Set it in Terminal first (it is only sent to Unpaywall):
    export UNPAYWALL_EMAIL=you@example.org
Then run:  python s4d_unpaywall.py      and afterwards step 4b and step 4c again.
"""
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from common import DATA, http_get, load, looks_like_gate, save
from s4_fetch_fulltext import TEXTS, epmc_xml, html_text, pdf_text

API = "https://api.unpaywall.org/v2/"


def lookup(doi, email):
    r = http_get(API + doi, params={"email": email})
    if r is None or r.status_code != 200:
        return []
    d = r.json()
    locs = ([d["best_oa_location"]] if d.get("best_oa_location") else []) + (d.get("oa_locations") or [])
    urls = []
    for loc in locs:
        for u in (loc.get("url_for_pdf"), loc.get("url_for_landing_page"), loc.get("url")):
            if u and u not in urls:
                urls.append(u)
    return urls


def get_text(urls):
    for u in urls:
        pmc = re.search(r"PMC\d{5,}", u)
        if pmc:  # PubMed Central pages refuse automated requests; Europe PMC serves the same article openly
            t = epmc_xml(pmc.group(0))
            if t:
                return t, f"ok: Unpaywall via Europe PMC ({pmc.group(0)})"
            continue
        r = http_get(u)
        if r is None or r.status_code != 200:
            continue
        if r.content[:4] == b"%PDF":
            try:
                return pdf_text(r.content), f"ok: Unpaywall PDF ({u[:60]})"
            except Exception:
                continue
        if "html" in r.headers.get("content-type", ""):
            t = html_text(r.content)
            if len(t) > 8000 and not looks_like_gate(t, "publication"):  # a full article page, not an abstract or login page
                return t, f"ok: Unpaywall web page ({u[:60]})"
    return None, None


def work(r, email):
    urls = lookup(r["doi"], email)
    if not urls:
        return r, None, "missing: no open-access copy in Unpaywall"
    text, status = get_text(urls)
    return r, text, status or "missing: Unpaywall copy could not be downloaded"


if __name__ == "__main__":
    email = os.environ.get("UNPAYWALL_EMAIL", "").strip()
    if "@" not in email:
        sys.exit("Set your email first:  export UNPAYWALL_EMAIL=you@example.org")
    sources = load("sources.json")
    todo = [r for recs in sources.values() for r in recs
            if r.get("decision") in ("Include", "Borderline") and r["kind"] == "publication" and r.get("doi")
            and not r.get("text_file") and not r.get("manual_pdf") and "Unpaywall" not in r.get("fulltext_status", "")]
    print(f"{len(todo)} missing papers with a DOI to look up", flush=True)
    found = 0
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i, fut in enumerate(as_completed([pool.submit(work, r, email) for r in todo]), 1):
            r, text, status = fut.result()
            r["fulltext_status"] = status
            if text:
                path = TEXTS / f"{r['source_id']}.txt"
                path.write_text(text); r["text_file"] = path.name; found += 1
            print(f"[{i}/{len(todo)}] {status[:45]:45s} {r['title'][:60]}", flush=True)
            if i % 10 == 0:
                save("sources.json", sources)
    save("sources.json", sources)
    print(f"found {found} free copies. Now run: python s4b_remove_duplicates.py  and  python s4c_missing_list.py")
