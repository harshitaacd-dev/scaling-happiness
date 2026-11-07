"""Step 4e: download missing papers through your Erasmus University library access, slowly and politely.

Runs a real browser window on YOUR computer. YOU log in to EUR yourself; your password never leaves your machine and
is never stored by this script (the browser keeps its own login cookies in .eur_browser/ so you log in once).

For each paper in data/missing_fulltexts.csv (made by step 4c) it opens the library link and saves the PDF into the
right folder under the right name. If it cannot find the PDF by itself, it waits so you can click the publisher's
PDF / Download button in the window; the file is caught and saved for you. Press Ctrl+C at any time to stop.

Library licences forbid fast bulk downloading, and publishers can block a whole university for it. This script
therefore waits 20-40 seconds between papers and stops after --max papers (default 40) per run. Please keep it so.

Setup (once):   pip install playwright      then      python -m playwright install chromium
Run:            python s4e_eur_downloader.py            (options: --max 40, --assist-seconds 90, --browser firefox|safari|chrome)
Afterwards:     python s4_fetch_fulltext.py   then   python s4b_remove_duplicates.py   then   python s4c_missing_list.py
"""
import argparse
import csv
import random
import re
import time
from urllib.parse import quote, urljoin

from common import DATA, ROOT

PROXY_HOST = "eur.idm.oclc.org"
PROXY = f"https://{PROXY_HOST}/login?url="
LOG = DATA / "eur_download_log.csv"
BLOCK_SIGNS = re.compile(r"captcha|unusual traffic|too many requests|access (has been )?(denied|blocked)|systematic download", re.I)


def proxied(url):
    return url if PROXY_HOST in url else PROXY + quote(url, safe="")


LOGIN_HOSTS = re.compile(r"login\.microsoftonline|surfconext|/sso|/idp/|shibboleth|/saml|login\.eur|myaccess|/login\?(?!url=)", re.I)


def is_login_page(page):
    """True when the browser shows a sign-in page (EUR/SURFconext/Microsoft) instead of the article."""
    try:
        if LOGIN_HOSTS.search(page.url):
            return True
        return page.locator("input[type=password]").count() > 0
    except Exception:
        return False


def is_pdf(data):
    return bool(data) and data[:4] == b"%PDF"


def find_pdf_links(page):
    """Candidate PDF links on a publisher page: the standard citation_pdf_url tag first, then PDF-looking links."""
    links = []
    try:
        meta = page.locator('meta[name="citation_pdf_url"]').first
        if meta.count():
            links.append(urljoin(page.url, meta.get_attribute("content") or ""))
    except Exception:
        pass
    for a in page.locator("a[href]").all()[:400]:
        try:
            href = a.get_attribute("href") or ""
            label = (a.inner_text(timeout=200) or "").strip().lower()
        except Exception:
            continue
        if re.search(r"\.pdf($|\?)|/pdf/|/pdfft|/doi/pdf|/content/pdf|download.*pdf|pdfdirect|epdf", href, re.I) or label in ("pdf", "download pdf", "view pdf", "full text pdf"):
            links.append(urljoin(page.url, href))
    seen, out = set(), []
    for u in links:
        if u and u not in seen:
            seen.add(u); out.append(u)
    return out[:8]


def try_links(context, links):
    for u in links:
        for target in (u, proxied(u)):
            try:
                resp = context.request.get(target, timeout=60_000)
                body = resp.body()
                if is_pdf(body):
                    return body
            except Exception:
                continue
    return None


def download_bytes(d):
    try:
        path = d.path()
        data = open(path, "rb").read() if path else None
        return data if is_pdf(data) else None
    except Exception:
        return None


def wait_for_user_pdf(page, context, seconds, downloads, n0):
    """Let the user click the PDF/download button; catch either a download or a PDF opened in a tab."""
    got = {}

    def on_response(resp):
        if "application/pdf" in (resp.headers.get("content-type") or "") and "url" not in got:
            got["url"] = resp.url

    context.on("response", on_response)
    end = time.time() + seconds
    try:
        while time.time() < end and not got and len(downloads) == n0:
            page.wait_for_timeout(1000)
    finally:
        context.remove_listener("response", on_response)
    if len(downloads) > n0:
        return download_bytes(downloads[-1])
    if "url" in got:
        return try_links(context, [got["url"]])
    return None


def live_page(context, page):
    """Return a usable tab: the current one, another open one, or a new one. None if the browser itself is gone."""
    try:
        if page is not None and not page.is_closed():
            return page
        open_pages = [p for p in context.pages if not p.is_closed()]
        return open_pages[0] if open_pages else context.new_page()
    except Exception:
        return None


def done_set():
    if not LOG.exists():
        return set()
    return {row["save_as"] for row in csv.DictReader(open(LOG, encoding="utf-8")) if row["result"].startswith("saved")}


def log(row, result):
    new = not LOG.exists()
    with open(LOG, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["time", "tool_id", "save_as", "title", "result"])
        w.writerow([time.strftime("%Y-%m-%d %H:%M"), row["tool_id"], row["save_as"], row["title"][:120], result])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=40, help="papers per run (keep it modest)")
    ap.add_argument("--assist-seconds", type=int, default=90, help="time to click the PDF button yourself when automatic finding fails (0 = never wait)")
    ap.add_argument("--browser", default="chromium", choices=["chromium", "chrome", "firefox", "safari"],
                    help="chromium (default), chrome (your installed Google Chrome), firefox, or safari (Safari's WebKit engine)")
    ap.add_argument("--headless", action="store_true", help=argparse.SUPPRESS)  # for testing only
    ap.add_argument("--no-login-wait", action="store_true", help=argparse.SUPPRESS)
    ap.add_argument("--chromium-path", default=None, help=argparse.SUPPRESS)  # testing on machines with a preinstalled browser
    ap.add_argument("--csv", default=str(DATA / "missing_fulltexts.csv"))
    ap.add_argument("--min-wait", type=float, default=20)
    ap.add_argument("--max-wait", type=float, default=40)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    rows = [r for r in csv.DictReader(open(args.csv, encoding="utf-8-sig"))
            if r["kind"] == "publication" and r.get("library_link (EUR proxy)") and (r.get("done (y/n)") or "").lower() != "y"]
    already = done_set()
    rows = [r for r in rows if r["save_as"] not in already and not (ROOT / r["save_in_folder"] / r["save_as"]).exists()]
    print(f"{len(rows)} papers to fetch; this run will do at most {args.max}.")
    if not rows:
        return

    with sync_playwright() as p:
        engine = {"chromium": p.chromium, "chrome": p.chromium, "firefox": p.firefox, "safari": p.webkit}[args.browser]
        extra = {}
        if args.browser == "chrome":
            extra["channel"] = "chrome"  # the Google Chrome installed on your computer
        if args.chromium_path:
            extra["executable_path"] = args.chromium_path
        try:
            context = engine.launch_persistent_context(str(ROOT / f".eur_browser_{args.browser}"), headless=args.headless,
                                                       accept_downloads=True, **extra)
        except Exception as e:
            install = {"chromium": "chromium", "chrome": "chrome", "firefox": "firefox", "safari": "webkit"}[args.browser]
            print(f"\nCould not start {args.browser}: {str(e).splitlines()[0][:200]}")
            print(f"Install it once with:   python -m playwright install {install}")
            return
        page = context.pages[0] if context.pages else context.new_page()
        downloads = []  # every download in any tab, for the whole session (some sites start the PDF download at once)

        def on_download(d):
            downloads.append(d)

        for pg in context.pages:
            pg.on("download", on_download)
        context.on("page", lambda pg: pg.on("download", on_download))
        if not args.no_login_wait:
            try:
                page.goto(rows[0]["library_link (EUR proxy)"], timeout=90_000)
            except Exception as e:
                print(f"\nThe library page did not load ({str(e).splitlines()[0][:150]}).")
                print(f"Type this address into the browser window yourself:  https://{PROXY_HOST}/login")
            input("\nLog in to EUR in the browser window (if asked), then come back here and press Enter to start... ")
        saved = 0
        for i, row in enumerate(rows[: args.max], 1):
            dest = ROOT / row["save_in_folder"] / row["save_as"]
            dest.parent.mkdir(parents=True, exist_ok=True)
            print(f"[{i}/{min(len(rows), args.max)}] {row['title'][:70]}", flush=True)
            page = live_page(context, page)
            if page is None:
                print("\nThe browser window was closed. Run the script again to continue (saved papers are skipped).")
                break
            data, result = None, ""
            n0 = len(downloads)
            try:
                try:
                    resp = page.goto(row["library_link (EUR proxy)"], wait_until="domcontentloaded", timeout=90_000)
                except Exception as e:
                    if "Download is starting" not in str(e):
                        raise
                    resp = None  # the link went straight to a file download
                page.wait_for_timeout(3000)
                if not (len(downloads) > n0) and is_login_page(page):
                    if args.no_login_wait:
                        result = "login required (EUR session expired)"
                        raise RuntimeError(result)
                    print("\n   Your EUR login has expired (the browser shows a sign-in page).")
                    input("   Log in again in the browser window, then press Enter here to continue... ")
                    page = live_page(context, page)
                    resp = page.goto(row["library_link (EUR proxy)"], wait_until="domcontentloaded", timeout=90_000)
                    page.wait_for_timeout(3000)
                    if is_login_page(page):
                        print("   Still on a sign-in page. Stopping; run the script again after logging in.")
                        log(row, "stopped: not logged in")
                        break
                if len(downloads) > n0:
                    data = download_bytes(downloads[-1])
                if not data and resp is not None and "application/pdf" in (resp.headers.get("content-type") or ""):
                    data = try_links(context, [page.url])
                text = page.locator("body").inner_text(timeout=5000)[:5000] if not data else ""
                if BLOCK_SIGNS.search(text):
                    print("\nThe publisher is showing a block or captcha page. Stopping to protect your library access.")
                    print("Solve it in the window if you like, wait a few hours, then run the script again.")
                    log(row, "stopped: block/captcha page")
                    break
                if not data:
                    data = try_links(context, find_pdf_links(page))
                if not data and args.assist_seconds:
                    print(f"   could not find the PDF automatically: click the PDF/Download button in the browser within {args.assist_seconds} s (or wait to skip)", flush=True)
                    data = wait_for_user_pdf(page, context, args.assist_seconds, downloads, n0)
            except KeyboardInterrupt:
                print("\nStopped by you."); break
            except Exception as e:
                result = result or f"error: {type(e).__name__}"
            if data:
                dest.write_bytes(data); saved += 1
                result = f"saved ({len(data) // 1024} KB)"
            else:
                result = result or "not found (try by hand, or ask the library)"
            print(f"   {result}", flush=True)
            log(row, result)
            if i < min(len(rows), args.max):
                time.sleep(random.uniform(args.min_wait, args.max_wait))
        context.close()
    print(f"\nSaved {saved} PDFs. Log: {LOG.relative_to(ROOT)}")
    print("Next: python s4_fetch_fulltext.py, then python s4b_remove_duplicates.py, then python s4c_missing_list.py")


if __name__ == "__main__":
    main()
