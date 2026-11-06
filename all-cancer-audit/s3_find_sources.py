"""Step 3: find and screen sources for every included tool.

Searches Europe PMC, PubMed, Crossref, ClinicalTrials.gov and WHO ICTRP (CTRI) with each tool's search terms,
plus a Claude web search for grey literature (company pages, FAQs, press, regulator pages), then screens every
record with the rule used for Niramai.
Output: data/sources.json  {tool_id: [source, ...]}  and data/search_log.json
"""
import csv
import re
import time
import datetime

from s1_discover_tools import ictrp
from common import DATA, ask_json, http_get, load, norm, save, web_research

TODAY = datetime.date.today().isoformat()
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"


def europepmc(q):
    out, cursor = [], "*"
    while True:
        r = http_get(EPMC, params=dict(query=q, format="json", resultType="core", pageSize=1000, cursorMark=cursor))
        if r is None or r.status_code != 200:
            return out, None
        d = r.json()
        for it in d.get("resultList", {}).get("result", []):
            urls = [u.get("url") for u in it.get("fullTextUrlList", {}).get("fullTextUrl", []) if u.get("availabilityCode") in ("OA", "F")]
            out.append(dict(kind="publication", db="Europe PMC", pmid=it.get("pmid"), pmcid=it.get("pmcid"), doi=(it.get("doi") or "").lower(),
                            title=it.get("title") or "", authors=it.get("authorString") or "", year=it.get("pubYear") or "",
                            venue=(it.get("journalInfo") or {}).get("journal", {}).get("title") or it.get("source"),
                            pubtype="; ".join(it.get("pubTypeList", {}).get("pubType", [])), abstract=it.get("abstractText") or "",
                            oa_urls=urls, url=f'https://europepmc.org/article/{it.get("source")}/{it.get("id")}'))
        nxt = d.get("nextCursorMark")
        if not nxt or nxt == cursor or len(out) >= d.get("hitCount", 0) or len(out) >= 2000:
            return out, d.get("hitCount", 0)
        cursor = nxt


def crossref(term, rx):
    r = http_get("https://api.crossref.org/works", params={"query.bibliographic": term, "rows": 200,
                 "select": "DOI,title,author,issued,container-title,type"})
    if r is None or r.status_code != 200:
        return [], None
    out = []
    for it in r.json()["message"]["items"]:
        title = " ".join(it.get("title") or [])
        if re.search(rx, title, re.I):
            out.append(dict(kind="publication", db="Crossref", doi=(it.get("DOI") or "").lower(), title=title,
                            authors=", ".join(f'{a.get("family", "")} {a.get("given", "")[:1]}' for a in (it.get("author") or [])[:6]),
                            year=str((it.get("issued", {}).get("date-parts") or [[None]])[0][0] or ""), venue=" ".join(it.get("container-title") or []),
                            pubtype=it.get("type"), abstract="", oa_urls=[], url=f'https://doi.org/{it.get("DOI")}'))
    return out, len(r.json()["message"]["items"])


def ctgov(term):
    q = f'"{term}"' if " " in term else term
    r = http_get("https://clinicaltrials.gov/api/v2/studies", params={"query.term": q, "pageSize": 200, "countTotal": "true"})
    if r is None or r.status_code != 200:
        return [], None
    out = []
    for s in r.json().get("studies", []):
        p = s["protocolSection"]; idm = p["identificationModule"]
        out.append(dict(kind="trial registration", db="ClinicalTrials.gov", trial_id=idm["nctId"], title=idm.get("officialTitle") or idm.get("briefTitle") or "",
                        authors=p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name") or "",
                        year=(p.get("statusModule", {}).get("studyFirstSubmitDate") or "")[:4], venue="ClinicalTrials.gov", pubtype="",
                        abstract=p.get("descriptionModule", {}).get("briefSummary", ""), oa_urls=[], url=f'https://clinicaltrials.gov/study/{idm["nctId"]}'))
    return out, r.json().get("totalCount")


GREY_PROMPT = """List every web page that is published by {company} about {tool}, or that reports on {tool} specifically:
product pages, publications/research pages, FAQs, white papers, press releases, news features, regulator or government pages
(CDSCO, state programmes, IndiaAI, NITI Aayog), and magazine features. Exclude pages that only mention the tool in passing.
Answer with one line per page in exactly this form:  URL | page title | page type"""

SCREEN_SCHEMA = {"type": "object", "properties": {"decisions": {"type": "array", "items": {
    "type": "object", "properties": {"id": {"type": "integer"}, "decision": {"type": "string", "enum": ["Include", "Borderline", "Exclude"]},
                                     "reason": {"type": "string"}}, "required": ["id", "decision", "reason"], "additionalProperties": False}}},
    "required": ["decisions"], "additionalProperties": False}
SCREEN_SYSTEM = """You screen sources for a transparency audit of one AI cancer tool, using this rule:
Include a source if it is a study of the tool (any design, including conference abstracts, preprints, trial registrations, case reports)
or a document by the tool's company or developers (papers, patents, technical papers, product pages, FAQs, press releases, magazine features).
Exclude: reviews, commentaries, guidelines or modelling papers by others that only mention the tool; studies that use the company's
hardware without the AI component; sources about a different product with a similar name; sources not about the tool.
Use Borderline when the title and abstract do not settle it. Judge only from what is given."""


def screen(tool, recs):
    decided = {}
    for i in range(0, len(recs), 60):
        batch = recs[i:i + 60]
        lines = [f"[{i + j}] {r['kind']} | {r.get('year', '')} | {r['title']} | {r.get('authors', '')[:80]} | {r.get('venue', '')}\n    {r.get('abstract', '')[:700]}"
                 for j, r in enumerate(batch)]
        prompt = f"TOOL: {tool['tool_name']} by {tool['company']} ({tool['modality']}; {tool['cancer_types']}).\n\nSOURCES:\n" + "\n".join(lines)
        for d in ask_json(SCREEN_SYSTEM, prompt, SCREEN_SCHEMA, effort="low")["decisions"]:
            decided[d["id"]] = d
    for k, r in enumerate(recs):
        d = decided.get(k, {"decision": "Borderline", "reason": "Not screened"})
        r["decision"], r["reason"] = d["decision"], d["reason"]
    return recs


def key(r):
    return ("T:" + r["trial_id"].upper()) if r.get("trial_id") else ("D:" + r["doi"]) if r.get("doi") else ("P:" + str(r["pmid"])) if r.get("pmid") else ("N:" + norm(r["title"])[:100])


if __name__ == "__main__":
    tools = [t for t in csv.DictReader(open(DATA / "corpus.csv")) if t["include"].strip().lower() == "yes"]
    sources = load("sources.json", {}); log = load("search_log.json", [])
    for t in tools:
        if t["tool_id"] in sources:
            continue
        print("==", t["tool_name"], flush=True)
        rx = t["name_regex"] or re.escape(t["tool_name"])
        recs = []
        for term in [s.strip() for s in t["search_terms"].split(";") if s.strip()]:
            for name, fn in (("Europe PMC", lambda: europepmc(term)), ("Crossref", lambda: crossref(term.strip('"'), rx)),
                             ("ClinicalTrials.gov", lambda: ctgov(term.strip('"'))), ("WHO ICTRP", lambda: (ictrp(term.strip('"')), None))):
                try:
                    got, hits = fn()
                except Exception as e:
                    got, hits = [], f"ERROR {e}"
                if name == "WHO ICTRP":
                    got = [dict(kind="trial registration", db="WHO ICTRP", trial_id=g["trial_id"], title=g["title"], authors="", year="", venue="CTRI",
                                pubtype="", abstract="", oa_urls=[], url=g["url"]) for g in got]
                log.append(dict(date=TODAY, tool_id=t["tool_id"], database=name, query=term, hits=hits, retrieved=len(got)))
                recs += got
                time.sleep(0.5)
        # grey literature
        try:
            text = web_research(GREY_PROMPT.format(company=t["company"], tool=t["tool_name"]), max_searches=10, effort="medium")
            for line in text.splitlines():
                m = re.match(r"\s*[-*]?\s*(https?://\S+)\s*\|\s*([^|]*)\|?\s*(.*)", line)
                if m:
                    recs.append(dict(kind="web page", db="Web search", title=m.group(2).strip(), authors=t["company"], year="", venue=m.group(3).strip(),
                                     pubtype="web page", abstract="", oa_urls=[m.group(1).rstrip(").,")], url=m.group(1).rstrip(").,")))
            log.append(dict(date=TODAY, tool_id=t["tool_id"], database="Claude web search", query=GREY_PROMPT.split("\n")[0].format(company=t["company"], tool=t["tool_name"]), hits=None, retrieved=sum(r["db"] == "Web search" for r in recs)))
        except Exception as e:
            print("grey literature search failed:", e)
        # dedupe; keep records that name the tool, plus all registry and web records
        merged = {}
        for r in recs:
            k = key(r)
            if k not in merged:
                merged[k] = r
            else:
                for f in ("abstract", "pmid", "pmcid", "doi"):
                    merged[k][f] = merged[k].get(f) or r.get(f)
                merged[k]["oa_urls"] = list(dict.fromkeys(merged[k]["oa_urls"] + r["oa_urls"]))
        cand = [r for r in merged.values() if r["kind"] != "publication" or re.search(rx, r["title"] + " " + r.get("abstract", ""), re.I)]
        dropped = len(merged) - len(cand)
        cand = screen(t, cand)
        sources[t["tool_id"]] = cand
        log.append(dict(date=TODAY, tool_id=t["tool_id"], database="(screening)", query="Niramai rule", hits=len(merged),
                        retrieved=sum(r["decision"] == "Include" for r in cand),
                        note=f"{dropped} publications dropped before screening (tool named only in full text)"))
        save("sources.json", sources); save("search_log.json", log)
        print(f"   {len(merged)} unique, {len(cand)} screened, include={sum(r['decision'] == 'Include' for r in cand)}", flush=True)
