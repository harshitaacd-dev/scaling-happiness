"""Deduplicate raw search records, match against existing library, flag relevance."""
import json, re, sys, difflib, html

raw = json.load(open(sys.argv[1])); lib = json.load(open(sys.argv[2])); OUT = sys.argv[3]
tools = {t["id"]: t for t in raw["tools"]}

def norm(t):
    t = html.unescape(re.sub(r"<[^>]+>", "", t or "")).lower()
    return re.sub(r"[^a-z0-9 ]", "", re.sub(r"\s+", " ", t)).strip()

# existing library: trial IDs only from registration sources themselves; titles for all
lib_trials = {i: s for s, v in lib.items() if v["type"] == "trial_registration" for i in v["ids"] if i.startswith(("CTRI", "NCT"))}
lib_dois = {i.lower(): s for s, v in lib.items() if v["type"] != "trial_registration" for i in v["ids"] if i.startswith("10.")}
lib_titles = [(norm(v["title"]), s) for s, v in lib.items() if v["title"] and v["title"] != "Not reported"]

def lib_match(r):
    if r.get("trial_id") and r["trial_id"] in lib_trials: return lib_trials[r["trial_id"]]
    if r.get("doi") and r["doi"] in lib_dois: return lib_dois[r["doi"]]
    n = norm(r.get("title"))
    if len(n) > 15:
        for lt, s in lib_titles:
            if len(lt) > 15 and (difflib.SequenceMatcher(None, n[:150], lt[:150]).ratio() > 0.88 or n.startswith(lt[:60]) or lt.startswith(n[:60])):
                return s
    return ""

merged = {}
def key(r):
    if r.get("trial_id"): return "T:" + r["trial_id"].upper()
    if r.get("doi"): return "D:" + r["doi"]
    if r.get("pmid"): return "P:" + str(r["pmid"])
    return "N:" + norm(r.get("title"))[:120]

# first pass: build alias map so the same paper found via DOI in one db and PMID in another merges
alias = {}
for r in raw["records"]:
    ks = [k for k in ("T:" + (r.get("trial_id") or "").upper() if r.get("trial_id") else None,
                      "D:" + r["doi"] if r.get("doi") else None,
                      "P:" + str(r["pmid"]) if r.get("pmid") else None,
                      "N:" + norm(r.get("title"))[:120] if len(norm(r.get("title"))) > 20 else None) if k]
    root = next((alias[k] for k in ks if k in alias), ks[0] if ks else None)
    for k in ks: alias.setdefault(k, root)

for r in raw["records"]:
    k = alias.get(key(r), key(r))
    m = merged.get(k)
    if m is None:
        m = merged[k] = dict(r); m["tool_ids"] = set(); m["databases"] = set()
    for f in ("pmid", "pmcid", "doi", "abstract", "authors", "venue", "year", "fulltext_url", "countries", "pubtype"):
        if not m.get(f) and r.get(f): m[f] = r[f]
    if r.get("open_access"): m["open_access"] = True
    if r["database"] == "Europe PMC" and r.get("fulltext_url"): m["fulltext_url"] = r["fulltext_url"]
    m["tool_ids"].add(r["tool_id"]); m["databases"].add(r["database"])

out = []
for k, m in merged.items():
    title = html.unescape(re.sub(r"<[^>]+>", "", m.get("title") or ""))
    ta = title + " " + html.unescape(re.sub(r"<[^>]+>", "", m.get("abstract") or ""))
    tids = sorted(m["tool_ids"])
    named = [t for t in tids if re.search(tools[t]["rx"], ta, re.I)]
    india = bool(re.search(r"india|indian|bangalore|bengaluru|delhi|mumbai|chennai|pune|kolkata|hyderabad|karnataka|maharashtra|kerala|tamil|punjab|ctri", ta + " " + (m.get("countries") or "") + " " + (m.get("trial_id") or ""), re.I))
    if m["kind"] == "trial registration":
        loc = "title" if named and re.search("|".join(tools[t]["rx"] for t in named), title, re.I) else ("title/summary" if named else "registry search hit only")
    else:
        loc = ("title/abstract" if named else ("abstract not available" if not m.get("abstract") else "full text only"))
    existing = lib_match(dict(m, title=title))
    # suggested screening decision
    if existing: sug, why = "Already in library", f"Matches {existing}"
    elif named and m["kind"] == "trial registration": sug, why = "Include", "Tool/company named in registration"
    elif named: sug, why = "Include", "Tool/company named in title/abstract"
    elif loc == "abstract not available" and re.search(tools[tids[0]]["rx"], title, re.I): sug, why = "Include", "Tool named in title"
    elif loc == "full text only": sug, why = "Check (secondary)", "Tool mentioned only in full text, e.g. a review; may describe tool's data"
    else: sug, why = "Check", "Search hit, tool not named in title/abstract"
    if "T07" in tids and sug == "Include": sug, why = "Check", "AIIMS search is not tool-specific; confirm it is the AIIMS/BPL mammography model"
    out.append(dict(key=k, tools="; ".join(tools[t]["label"] for t in tids), tool_ids=tids, kind=m["kind"],
        trial_id=m.get("trial_id", ""), title=title, authors=m.get("authors") or "", year=m.get("year") or "", venue=m.get("venue") or "",
        pubtype=m.get("pubtype") or "", doi=m.get("doi") or "", pmid=m.get("pmid") or "", pmcid=m.get("pmcid") or "",
        open_access="Yes" if m.get("open_access") else ("No/unknown"), link=m.get("fulltext_url") or "",
        databases="; ".join(sorted(m["databases"])), mention=loc, india=("Yes" if india else "Not stated"),
        existing=existing, suggestion=sug, reason=why, abstract=(m.get("abstract") or "")[:1500]))

json.dump(dict(date=raw["date"], tools=raw["tools"], log=raw["log"], items=out), open(OUT, "w"), indent=1)
from collections import Counter
print("unique:", len(out)); print(Counter(o["suggestion"] for o in out))
for t in raw["tools"]:
    c = Counter(o["suggestion"] for o in out if t["id"] in o["tool_ids"]); print(t["id"], t["label"][:28], dict(c))
