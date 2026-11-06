"""Shared helpers for the all-cancer AI tool audit pipeline."""
import html
import json
import os
import re
import threading
import time
from pathlib import Path

import anthropic
import requests
import openpyxl

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)
TEMPLATE = ROOT.parent / "extraction-tables" / "niramai_thermalytix_extraction_table.xlsx"
MODEL = os.environ.get("AUDIT_MODEL", "claude-opus-5-5")

_client = None


def client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(max_retries=4)
    return _client


HTTP = requests.Session()
HTTP.headers["User-Agent"] = "academic-literature-audit/1.0 (research; contact via repository)"


def _get_in_thread(url, kw, box):
    try:
        box["r"] = requests.get(url, timeout=(10, 30), headers=HTTP.headers, **kw)
    except Exception as e:  # reported to the caller as a failed attempt
        box["e"] = e


def http_get(url, tries=2, deadline=60, **kw):
    """GET with a hard wall-clock limit per attempt, so a slow or stalled website cannot hang the run.

    Each attempt runs in a background thread; if it has not finished within `deadline` seconds it is
    abandoned. Returns a requests.Response or None.
    """
    for i in range(tries):
        box = {}
        t = threading.Thread(target=_get_in_thread, args=(url, kw, box), daemon=True)
        t.start(); t.join(deadline)
        r = box.get("r")
        if t.is_alive() or r is None:
            time.sleep(2 ** (i + 1)); continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 ** (i + 1)); continue
        return r
    return None


def norm(t):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or "")).lower()
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", t)).strip()


def load(name, default=None):
    p = DATA / name
    return json.loads(p.read_text()) if p.exists() else default


def save(name, obj):
    (DATA / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False))


# ---------------------------------------------------------------- Claude calls
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def _final_text(msg):
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"Request declined: {getattr(msg.stop_details, 'category', None)}")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("Output hit max_tokens; raise max_tokens or split the input")
    return "".join(b.text for b in msg.content if b.type == "text")


def ask_json(system, content, schema, effort="medium", max_tokens=64000):
    """One Claude call that must return JSON matching `schema` (structured outputs)."""
    with client().beta.messages.stream(
        model=MODEL,
        max_tokens=max_tokens,
        betas=[FALLBACK_BETA],
        fallbacks="default",  # re-runs on a fallback model if the request is declined
        system=system,
        messages=[{"role": "user", "content": content}],
        output_config={"effort": effort, "format": {"type": "json_schema", "schema": schema}},
    ) as stream:
        msg = stream.get_final_message()
    return json.loads(_final_text(msg))


def web_research(prompt, max_searches=20, effort="high"):
    """Claude with the server-side web search tool; returns the final text answer."""
    messages = [{"role": "user", "content": prompt}]
    for _ in range(10):  # continue through pause_turn
        with client().beta.messages.stream(
            model=MODEL,
            max_tokens=64000,
            betas=[FALLBACK_BETA],
            fallbacks="default",
            output_config={"effort": effort},
            tools=[{"type": "web_search_20260209", "name": "web_search", "max_uses": max_searches}],
            messages=messages,
        ) as stream:
            msg = stream.get_final_message()
        if msg.stop_reason == "pause_turn":
            messages.append({"role": "assistant", "content": msg.content})
            continue
        return _final_text(msg)
    raise RuntimeError("Web research did not finish")


# ---------------------------------------------------------------- template labels
def template_labels():
    """Data-point and STANDING Together item labels, read from the Niramai template."""
    ws = openpyxl.load_workbook(TEMPLATE)["Niramai (Thermalytix)"]
    dps = [ws.cell(r, 2).value for r in range(13, 23)]
    items = [(ws.cell(r, 1).value, ws.cell(r, 2).value) for r in range(26, 55)]
    return dps, items


def safe_sheet_name(s):
    s = re.sub(r"[\[\]\:\*\?\/\\]", "-", s)
    return s[:31]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:50]
