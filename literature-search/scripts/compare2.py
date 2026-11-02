"""Compare the verification search with search 1 + library; keep only genuinely new records."""
import json, re, sys, html
from collections import Counter, defaultdict

r2 = json.load(open(sys.argv[1])); s1 = json.load(open(sys.argv[2])); lib = json.load(open(sys.argv[3])); OUT = sys.argv[4]
tools = {t["id"]: t for t in s1["tools"]}
TOOLRX = {t["id"]: t["rx"] for t in s1["tools"]}
TOOLRX.update({"T12": r"\bupath\b", "T04": r"automated visual evaluation|(?-i:\b(?:n?AVE|PAVE)\b)", "T02": r"smart[ -]?scope|periwinkle tech", "T05": r"mobile ?odt|visual ?check|enhanced visual assessment|\bEVA (system|colposcope|device)",
               "T06": r"cervastra|aindra|intellistain", "T10": r"ibreastexam|ue life ?sciences|intelligent breast exam|\biBE\b"})

def norm(t):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or "")).lower()
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", t)).strip()

known = set()
for o in s1["items"]:
    for k in (o.get("trial_id"), o.get("doi"), str(o.get("pmid") or ""), norm(o.get("title"))[:100]):
        if k and len(k) > 5: known.add(k.upper() if k.startswith(("CTRI", "NCT")) else k)
for v in lib.values():
    for i in v["ids"]: known.add(i.lower() if i.startswith("10.") else i)
    if v["title"]: known.add(norm(v["title"])[:100])

def keys(o):
    ks = [o.get("trial_id") and o["trial_id"].upper(), o.get("doi"), str(o.get("pmid") or ""), norm(o.get("title"))[:100]]
    return [k for k in ks if k and len(k) > 5]

PRODUCT = r"®|™|\b(device|app|application|smartphone|mobile|handheld|hand-held|point[- ]of[- ]care|portable|low[- ]cost|commercial|software|platform|start-?up|thermograph|thermal)\b"
new = {}
for o in r2["records"]:
    ks = keys(o)
    if not ks or any(k in known for k in ks): continue
    k = ks[0]
    m = new.setdefault(k, dict(o, strategies=set(), dbs=set(), via=set()))
    for f in ("abstract", "pmid", "doi", "open_access", "fulltext_url", "authors", "venue", "year"):
        if not m.get(f) and o.get(f): m[f] = o[f]
    m["strategies"].add(o["strategy"]); m["dbs"].add(o["database"])
    if o.get("via"): m["via"].add(o["via"])
# merge entries sharing secondary keys
seen, items = {}, []
for k, m in new.items():
    alt = [x for x in keys(m) if x in seen]
    if alt:
        t = seen[alt[0]]; t["strategies"] |= m["strategies"]; t["dbs"] |= m["dbs"]; t["via"] |= m["via"]; continue
    for x in keys(m): seen[x] = m
    items.append(m)

out = []
for m in items:
    title = html.unescape(re.sub(r"<[^>]+>", "", m.get("title") or "")); ab = html.unescape(re.sub(r"<[^>]+>", "", m.get("abstract") or ""))
    named = [tid for tid, rx in TOOLRX.items() if rx and re.search(rx, title + " " + ab, re.I)]
    if "T07" in named and not re.search(r"AIIMS|All India Institute|BPL", title + " " + ab + " " + (m.get("authors") or ""), re.I): named.remove("T07")
    if m["tool_id"] not in ("topic",) and m["tool_id"] in TOOLRX and m["tool_id"] not in named and m["strategy"] != "C citations":
        pass
    india = bool(re.search(r"india|indian|ctri", title + " " + ab + " " + (m.get("trial_id") or ""), re.I))
    if named:
        dec, why = "Include", f"Names {', '.join(tools[t]['label'] for t in named)}"
        if "T07" in named and len(named) == 1: dec, why = "Check", "AIIMS-related; confirm it is the AIIMS/BPL mammography model"
    elif m["strategy"] == "D topic":
        prod = re.findall(PRODUCT, title + " " + ab, re.I)
        dec, why = ("Check: possible other tool", "Indian AI screening study naming a device/app/product: may be a tool not on our list") if prod else \
                   ("Topic only", "Indian AI screening research; no product named (likely academic model, not a deployed tool)")
    elif m["strategy"] == "A variants" and ab:
        dec, why = "Secondary (full text)", "Variant term found only in full text (e.g. a review)"
    else:
        dec, why = "Check", "Found via variant/citation search; tool not named in title/abstract"
    out.append(dict(tool=", ".join(tools[t]["label"] for t in named) if named else ("(topic search)" if m["tool_id"] == "topic" else tools.get(m["tool_id"], {}).get("label", "")),
        kind=m["kind"], year=m.get("year") or "", title=title, authors=m.get("authors") or "", venue=m.get("venue") or "",
        ident=m.get("trial_id") or (f'doi:{m["doi"]}' if m.get("doi") else (f'PMID:{m["pmid"]}' if m.get("pmid") else "")),
        open_access="Yes" if m.get("open_access") else "No/unknown", link=m.get("fulltext_url") or "", india="Yes" if india else "Not stated",
        strategy="; ".join(sorted(m["strategies"])), found_in="; ".join(sorted(m["dbs"])), via="; ".join(sorted(m["via"]))[:300],
        decision=dec, why=why, abstract=ab[:1500]))
json.dump(dict(date=r2["date"], log=r2["log"], items=out), open(OUT, "w"), indent=1)
print("new unique records:", len(out)); print(Counter(o["decision"] for o in out))
print(Counter((o["strategy"], o["decision"]) for o in out))
