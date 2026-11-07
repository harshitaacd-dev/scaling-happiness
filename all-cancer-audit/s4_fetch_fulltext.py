"""Step 4: get the full text of every Include/Borderline source.

Order of attempts: your own PDFs in manual_pdfs/<tool_id>/  ->  Europe PMC full-text XML (open access)
->  open-access PDF links  ->  trial registry pages  ->  web pages.
Texts are saved to data/texts/<source_id>.txt with '=== PAGE n ===' markers (PDFs) so quotes can carry page numbers.
Paywalled papers: download them yourself (e.g. with your library proxy), put them in manual_pdfs/<tool_id>/ and re-run.
A PDF in that folder is matched to a source by title; if none matches it is added as a new source.
Output: data/sources.json updated with source_id, text_file, fulltext_status.
Downloads run 8 at a time. Sources already marked missing are skipped on re-runs; add --retry-missing to try them again.
"""
import io
import re
from pathlib import Path

from bs4 import BeautifulSoup
from pypdf import PdfReader

from common import DATA, ROOT, http_get, load, looks_like_gate, norm, save, slug

TEXTS = DATA / "texts"; TEXTS.mkdir(exist_ok=True)
MANUAL = ROOT / "manual_pdfs"; MANUAL.mkdir(exist_ok=True)


def pdf_text(data):
    reader = PdfReader(io.BytesIO(data))
    return "\n".join(f"=== PAGE {i + 1} ===\n{(p.extract_text() or '').strip()}" for i, p in enumerate(reader.pages))


def html_text(data):
    soup = BeautifulSoup(data, "html.parser")
    for t in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        t.decompose()
    return "=== WEB PAGE (no page numbers) ===\n" + re.sub(r"\n\s*\n+", "\n\n", soup.get_text("\n", strip=True))


def epmc_xml(pmcid):
    r = http_get(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML")
    if r is None or r.status_code != 200 or "<body" not in r.text:
        return None
    soup = BeautifulSoup(r.text, "xml")
    parts = [soup.find("article-title").get_text(" ", strip=True) if soup.find("article-title") else ""]
    if soup.find("abstract"):
        parts.append("ABSTRACT\n" + soup.find("abstract").get_text("\n", strip=True))
    parts.append(soup.find("body").get_text("\n", strip=True))
    for tw in soup.find_all("table-wrap"):
        parts.append("TABLE\n" + tw.get_text(" | ", strip=True))
    return "=== FULL TEXT (Europe PMC XML; no page numbers) ===\n" + "\n\n".join(parts)


def fetch(src):
    if src["kind"] == "trial registration":
        if src.get("trial_id", "").startswith("NCT"):
            r = http_get(f"https://clinicaltrials.gov/api/v2/studies/{src['trial_id']}")
            if r is not None and r.status_code == 200:
                return "=== TRIAL REGISTRATION (ClinicalTrials.gov record; no page numbers) ===\n" + re.sub(r'[{}\[\]"]', " ", r.text), "ok: registry"
        r = http_get(src["url"])
        if r is not None and r.status_code == 200:
            return "=== TRIAL REGISTRATION (WHO ICTRP record; no page numbers) ===\n" + html_text(r.content).split("\n", 1)[1], "ok: registry"
        return None, "failed: registry page"
    if src.get("pmcid"):
        t = epmc_xml(src["pmcid"])
        if t:
            return t, "ok: Europe PMC XML"
    for u in src.get("oa_urls", []) + ([src["url"]] if src["kind"] == "web page" else []):
        r = http_get(u)
        if r is None or r.status_code != 200:
            continue
        if r.content[:4] == b"%PDF":
            try:
                return pdf_text(r.content), "ok: PDF"
            except Exception:
                continue
        if src["kind"] == "web page" or "html" in r.headers.get("content-type", ""):
            t = html_text(r.content)
            if len(t) > 1500 and not looks_like_gate(t, src["kind"]):
                return t, "ok: web page"
    return None, "missing: no open-access full text (add the PDF to manual_pdfs/)"


if __name__ == "__main__":
    import sys
    from concurrent.futures import ThreadPoolExecutor, as_completed
    RETRY = "--retry-missing" in sys.argv
    WORKERS = 8
    sources = load("sources.json")
    todo = []
    for tool_id, recs in sources.items():
        # PDFs you added by hand
        for pdf in sorted((MANUAL / tool_id).glob("*.pdf")) if (MANUAL / tool_id).exists() else []:
            text = pdf_text(pdf.read_bytes())
            if looks_like_gate(text, "publication"):
                print(f"WARNING: {pdf.relative_to(ROOT)} looks like a login or paywall page, not the paper. Skipped; replace it.")
                continue
            head = norm(text[:3000])
            # a file named <source_id>.pdf (as listed by step 4c) is matched exactly; otherwise match by title
            match = next((r for r in recs if r.get("source_id") == pdf.stem), None) or \
                next((r for r in recs if r.get("title") and norm(r["title"])[:60] in head), None)
            if match is None:
                match = dict(kind="publication", db="Manual PDF", title=pdf.stem, authors="", year="", venue="", pubtype="", abstract="",
                             oa_urls=[], url="", decision="Include", reason="Added by hand")
                recs.append(match)
            if match.get("manual_pdf") == str(pdf.relative_to(ROOT)) and match.get("text_file"):
                continue  # already read on an earlier run
            match["manual_pdf"] = str(pdf.relative_to(ROOT)); match["decision"] = "Include"
            match["_text"] = text
        for k, r in enumerate(recs):
            if r.get("decision") not in ("Include", "Borderline"):
                continue
            r.setdefault("source_id", f"{tool_id}__{k:03d}")
            path = TEXTS / f"{r['source_id']}.txt"
            if "_text" in r:
                path.write_text(r.pop("_text")); r["text_file"] = path.name; r["fulltext_status"] = "ok: manual PDF"
            elif path.exists():  # saved by an earlier, interrupted run
                r["text_file"] = path.name
                r.setdefault("fulltext_status", "ok: saved earlier")
            elif r.get("fulltext_status", "").startswith(("missing", "failed")) and not RETRY:
                pass  # already tried; use --retry-missing to try again
            else:
                todo.append((tool_id, r, path))
    save("sources.json", sources)

    # download several sources at once, so one slow website does not hold up the rest
    print(f"{len(todo)} sources to download ({WORKERS} at a time)", flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(fetch, r): (tool_id, r, path) for tool_id, r, path in todo}
        for fut in as_completed(futures):
            tool_id, r, path = futures[fut]
            try:
                text, status = fut.result()
            except Exception as e:  # one bad page must not stop the run
                text, status = None, f"failed: {type(e).__name__}"
            r["fulltext_status"] = status
            if text:
                path.write_text(text); r["text_file"] = path.name
            done += 1
            print(f"[{done}/{len(todo)}] {tool_id[:28]:28s} {status[:34]:34s} {r['title'][:55]}", flush=True)
            if done % 10 == 0:
                save("sources.json", sources)
    save("sources.json", sources)
    n = sum(1 for v in sources.values() for r in v if r.get("text_file"))
    m = sum(1 for v in sources.values() for r in v if r.get("decision") in ("Include", "Borderline") and not r.get("text_file"))
    print(f"full texts: {n}; still missing: {m} (see data/sources.json, fulltext_status)")
