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


GATE = re.compile(r"sign in|log ?in|password|single sign-on|institutional (access|login)|access through your institution|"
                  r"purchase (this )?(article|pdf)|buy (this )?article|subscribe to (read|continue)|rent this article|"
                  r"enable (javascript|cookies)|verify you are (a )?human|captcha|access denied|403 forbidden", re.I)
ARTICLE = re.compile(r"\b(abstract|introduction|methods?|results|discussion|conclusions?|references)\b", re.I)


def looks_like_gate(text, kind="publication"):
    """True if a saved text looks like a login, paywall, cookie or bot-check page rather than the document.

    Papers must show article structure; company/news web pages often have 'Log in' in their menus, so for them
    only short pages dominated by login/paywall wording are treated as gates.
    """
    if not text:
        return True
    body = text[:30000]
    gates = len(GATE.findall(body))
    if kind == "publication":
        sections = len(set(m.lower() for m in ARTICLE.findall(body)))
        return (len(text) < 25000 and gates >= 2 and sections < 3) or (len(text) < 4000 and gates >= 1)
    return len(text) < 6000 and gates >= 2


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
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],  # same for every source: cached
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


def calibration_examples(per_score=2, max_len=220):
    """Scoring standard taken from the Niramai reference table: for each of the 29 items, short examples of what was
    scored 2 and 1 there (value and quote), preferring examples from different source types."""
    ws = openpyxl.load_workbook(TEMPLATE)["Niramai (Thermalytix)"]
    lines = []
    for i, r in enumerate(range(26, 55)):
        label = ws.cell(r, 2).value
        block = [f"it{i + 1:02d} {label}"]
        for score in (2, 1):
            seen_types, n = set(), 0
            for k in range(50):
                c0 = 3 + 4 * k
                v, q, sc = ws.cell(r, c0).value, ws.cell(r, c0 + 1).value, ws.cell(r, c0 + 3).value
                stype = (ws.cell(4, c0).value or "").split(" ")[0].lower()
                if sc != score or not v or str(v).startswith("Not reported") or stype in seen_types:
                    continue
                seen_types.add(stype); n += 1
                quote = re.sub(r"\s+", " ", str(q or ""))[:max_len]
                block.append(f"   scored {score} ({stype}): {re.sub(r'\s+', ' ', str(v))[:max_len]} | quote: {quote}")
                if n >= per_score:
                    break
        lines.append("\n".join(block))
    return "\n".join(lines)


def safe_sheet_name(s):
    s = re.sub(r"[\[\]\:\*\?\/\\]", "-", s)
    return s[:31]


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")[:50]
