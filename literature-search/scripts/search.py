"""Systematic search for literature and trial registrations on AI breast/cervical
cancer screening tools deployed in India.

Databases: Europe PMC (includes PubMed/MEDLINE, PMC full text, preprints),
PubMed (E-utilities), Crossref, ClinicalTrials.gov (API v2), WHO ICTRP (covers CTRI).
Every query is logged with date, database, hit count and records retrieved.
Raw results are written to a JSON file for the workbook builder.
"""
import json, re, sys, time, datetime
import requests
from bs4 import BeautifulSoup

OUT = sys.argv[1]
TODAY = datetime.date.today().isoformat()
S = requests.Session()
S.headers["User-Agent"] = "dissertation-literature-search/1.0 (academic research)"

# tool id, label, search terms (each run separately), relevance regex for title/abstract
TOOLS = [
    ("T01", "Thermalytix (Niramai)", ['"Thermalytix"', '"Niramai"'], r"thermalytix|niramai"),
    ("T02", "Smart Scope CX (Periwinkle)", ['"Smart Scope" AND (cervical OR cervix)', '"Periwinkle Technologies"'], r"smart ?scope|periwinkle tech"),
    ("T03", "CanAssist Breast (OncoStem)", ['"CanAssist"', '"OncoStem"'], r"canassist|oncostem"),
    ("T04", "Automated Visual Evaluation (NCI/IARC)", ['"automated visual evaluation" AND (cervical OR cervix)'], r"automated visual evaluation|\bn?AVE\b|\bPAVE\b"),
    ("T05", "EVA VisualCheck (MobileODT)", ['"MobileODT"', '"VisualCheck"', '"Enhanced Visual Assessment" AND (cervical OR cervix)'], r"mobileodt|visual ?check|enhanced visual assessment|\bEVA\b"),
    ("T06", "CervAstra (Aindra)", ['"CervAstra"', '"Aindra"'], r"cervastra|aindra"),
    ("T07", "AIIMS mammography AI", ['"All India Institute of Medical Sciences" AND mammography AND ("artificial intelligence" OR "deep learning")'], r"mammogra"),
    ("T08", "MammoAssist (Telerad Tech)", ['"MammoAssist"', '"Telerad Tech"'], r"mammoassist|telerad"),
    ("T09", "Lord's Mark AI thermal device", ['"Lord\'s Mark" AND breast', '"Lords Mark" AND breast'], r"lord'?s mark"),
    ("T10", "iBreastExam (UE LifeSciences)", ['"iBreastExam"', '"UE LifeSciences"', '"intelligent breast exam"'], r"ibreastexam|ue lifesciences|intelligent breast exam|\biBE\b"),
    ("T11", "CytoSiA (OptraSCAN)", ['"CytoSiA"', '"OptraSCAN"'], r"cytosia|optrascan"),
    ("T12", "uPath HER2 (Roche)", ['"uPath" AND HER2'], r"upath"),
    ("T13", "MedXAI cervical AI", ['"MedXAI"'], r"medxai"),
]
# simpler keyword form for registries / Crossref (no boolean syntax)
REG_TERMS = {
    "T01": ["Thermalytix", "Niramai"], "T02": ["Smart Scope", "Periwinkle Technologies"], "T03": ["CanAssist", "OncoStem"],
    "T04": ["automated visual evaluation"], "T05": ["MobileODT", "VisualCheck", "Enhanced Visual Assessment"],
    "T06": ["CervAstra", "Aindra"], "T07": ["mammography artificial intelligence AIIMS"], "T08": ["MammoAssist", "Telerad"],
    "T09": ["Lord's Mark"], "T10": ["iBreastExam", "UE LifeSciences"], "T11": ["CytoSiA", "OptraSCAN"],
    "T12": ["uPath HER2"], "T13": ["MedXAI"],
}

log, records = [], []

def get(url, **kw):
    for i in range(5):
        try:
            r = S.get(url, timeout=90, **kw)
            if r.status_code == 429 or r.status_code >= 500:
                time.sleep(2 ** (i + 1)); continue
            return r
        except requests.RequestException:
            time.sleep(2 ** (i + 1))
    return None

def logq(db, tid, q, hits, got, note=""):
    log.append(dict(date=TODAY, database=db, tool_id=tid, query=q, hits=hits, retrieved=got, note=note))
    print(f"{db:18s} {tid} {q[:60]:60s} hits={hits} got={got} {note}", flush=True)

# ---------- Europe PMC ----------
def europepmc(tid, q):
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    cursor, got, hits = "*", 0, None
    while True:
        r = get(url, params=dict(query=q, format="json", resultType="core", pageSize=1000, cursorMark=cursor))
        if r is None or r.status_code != 200:
            logq("Europe PMC", tid, q, hits, got, "ERROR"); return
        d = r.json(); hits = d.get("hitCount", 0)
        for it in d.get("resultList", {}).get("result", []):
            urls = [u.get("url") for u in it.get("fullTextUrlList", {}).get("fullTextUrl", []) if u.get("availabilityCode") in ("OA", "F")]
            records.append(dict(tool_id=tid, database="Europe PMC", kind="publication",
                id_epmc=f'{it.get("source")}:{it.get("id")}', pmid=it.get("pmid"), pmcid=it.get("pmcid"), doi=(it.get("doi") or "").lower(),
                title=it.get("title"), authors=it.get("authorString"), year=it.get("pubYear"),
                venue=it.get("journalInfo", {}).get("journal", {}).get("title") or it.get("bookOrReportDetails", {}).get("publisher") or it.get("source"),
                pubtype="; ".join(it.get("pubTypeList", {}).get("pubType", [])), abstract=it.get("abstractText") or "",
                open_access=it.get("isOpenAccess") == "Y", fulltext_url=urls[0] if urls else (f'https://europepmc.org/article/{it.get("source")}/{it.get("id")}')))
            got += 1
        nxt = d.get("nextCursorMark")
        if not nxt or nxt == cursor or got >= hits or got >= 2000: break
        cursor = nxt
    logq("Europe PMC", tid, q, hits, got)

# ---------- PubMed ----------
def pubmed(tid, q):
    r = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=dict(db="pubmed", term=q, retmode="json", retmax=1000))
    if r is None or r.status_code != 200: logq("PubMed", tid, q, None, 0, "ERROR"); return
    d = r.json()["esearchresult"]; ids = d.get("idlist", [])
    for i in range(0, len(ids), 200):
        time.sleep(0.4)
        s = get("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi", params=dict(db="pubmed", id=",".join(ids[i:i+200]), retmode="json"))
        res = s.json()["result"] if s is not None and s.status_code == 200 else {}
        for pid in ids[i:i+200]:
            it = res.get(pid, {})
            doi = next((a["value"] for a in it.get("articleids", []) if a.get("idtype") == "doi"), "")
            pmc = next((a["value"] for a in it.get("articleids", []) if a.get("idtype") == "pmc"), "")
            records.append(dict(tool_id=tid, database="PubMed", kind="publication", pmid=pid, pmcid=pmc, doi=doi.lower(),
                title=it.get("title"), authors=", ".join(a["name"] for a in it.get("authors", [])[:6]), year=(it.get("pubdate") or "")[:4],
                venue=it.get("fulljournalname"), pubtype="; ".join(it.get("pubtype", [])), abstract="",
                open_access=bool(pmc), fulltext_url=f"https://pubmed.ncbi.nlm.nih.gov/{pid}/"))
    logq("PubMed", tid, q, int(d.get("count", 0)), len(ids))
    time.sleep(0.4)

# ---------- Crossref ----------
def crossref(tid, term, rx):
    r = get("https://api.crossref.org/works", params={"query.bibliographic": term, "rows": 200,
            "select": "DOI,title,author,issued,container-title,type,publisher"})
    if r is None or r.status_code != 200: logq("Crossref", tid, term, None, 0, "ERROR"); return
    items = r.json()["message"]["items"]; kept = 0
    for it in items:
        title = " ".join(it.get("title") or [])
        if not re.search(rx, title, re.I): continue   # Crossref is fuzzy: keep only exact title matches
        kept += 1
        records.append(dict(tool_id=tid, database="Crossref", kind="publication", doi=(it.get("DOI") or "").lower(), title=title,
            authors=", ".join(f'{a.get("family","")} {a.get("given","")[:1]}' for a in (it.get("author") or [])[:6]),
            year=str((it.get("issued", {}).get("date-parts") or [[None]])[0][0] or ""), venue=" ".join(it.get("container-title") or []) or it.get("publisher"),
            pubtype=it.get("type"), abstract="", open_access=None, fulltext_url=f'https://doi.org/{it.get("DOI")}'))
    logq("Crossref", tid, term, len(items), kept, "top 200 relevance-ranked; kept only titles matching tool name")
    time.sleep(1)

# ---------- ClinicalTrials.gov ----------
def ctgov(tid, term):
    r = get("https://clinicaltrials.gov/api/v2/studies", params={"query.term": (f'"{term}"' if " " in term else term), "pageSize": 200, "countTotal": "true"})
    if r is None or r.status_code != 200: logq("ClinicalTrials.gov", tid, term, None, 0, "ERROR"); return
    d = r.json(); st = d.get("studies", [])
    for s in st:
        p = s["protocolSection"]; idm = p["identificationModule"]
        records.append(dict(tool_id=tid, database="ClinicalTrials.gov", kind="trial registration", trial_id=idm["nctId"],
            title=idm.get("officialTitle") or idm.get("briefTitle"), authors=p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name"),
            year=(p.get("statusModule", {}).get("studyFirstSubmitDate") or "")[:4], venue="ClinicalTrials.gov",
            pubtype=p.get("statusModule", {}).get("overallStatus"), abstract=p.get("descriptionModule", {}).get("briefSummary", ""),
            countries="; ".join(sorted({l.get("country", "") for l in p.get("contactsLocationsModule", {}).get("locations", [])})),
            open_access=True, fulltext_url=f'https://clinicaltrials.gov/study/{idm["nctId"]}'))
    logq("ClinicalTrials.gov", tid, term, d.get("totalCount"), len(st))

# ---------- WHO ICTRP ----------
def ictrp(tid, term):
    try:
        s = requests.Session(); s.headers["User-Agent"] = "Mozilla/5.0"
        r = s.get("https://trialsearch.who.int/", timeout=90)
        soup = BeautifulSoup(r.text, "html.parser")
        data = {i.get("name"): i.get("value", "") for i in soup.select("input[type=hidden]") if i.get("name")}
        data.update({"TextBox1": term, "Button1": "Search"})
        r2 = s.post("https://trialsearch.who.int/", data=data, timeout=180)
        soup = BeautifulSoup(r2.text, "html.parser")
        txt = soup.get_text(" ", strip=True)
        m = re.search(r"(?:(\d+) records? for )?(\d+) trials? found", txt)
        hits = int(m.group(2)) if m else 0
        # if more than 10, switch page size to 100
        if hits > 10:
            data = {i.get("name"): i.get("value", "") for i in soup.select("input[type=hidden]") if i.get("name")}
            sel = soup.find("select")
            if sel is not None:
                data[sel.get("name")] = "100"; data["__EVENTTARGET"] = sel.get("name")
                r3 = s.post("https://trialsearch.who.int/", data=data, timeout=180)
                soup = BeautifulSoup(r3.text, "html.parser")
        got = 0
        for a in soup.find_all("a", href=re.compile(r"Trial2\.aspx\?TrialID=", re.I)):
            tr = a.find_parent("tr"); cells = [c.get_text(" ", strip=True) for c in tr.find_all("td")] if tr else []
            trial = re.search(r"TrialID=([^&]+)", a["href"]).group(1).strip()
            title = a.get_text(" ", strip=True)
            date = next((c for c in cells if re.match(r"^\d{4}-\d{2}-\d{2}$", c)), "")
            status = cells[0] if cells else ""
            records.append(dict(tool_id=tid, database="WHO ICTRP", kind="trial registration", trial_id=trial, title=title, authors="",
                year=date[:4], venue=("CTRI" if trial.startswith("CTRI") else "ICTRP"), pubtype=status, abstract="", open_access=True,
                fulltext_url="https://trialsearch.who.int/" + a["href"].lstrip("./")))
            got += 1
        logq("WHO ICTRP", tid, term, max(hits, got), got)
    except Exception as e:
        logq("WHO ICTRP", tid, term, None, 0, f"ERROR {e}")
    time.sleep(2)

for tid, label, qs, rx in TOOLS:
    for q in qs:
        europepmc(tid, q); pubmed(tid, q)
    for t in REG_TERMS[tid]:
        if tid != "T07": crossref(tid, t, rx)
        ctgov(tid, t); ictrp(tid, t)

json.dump(dict(date=TODAY, tools=[dict(id=t[0], label=t[1], queries=t[2], rx=t[3], reg_terms=REG_TERMS[t[0]]) for t in TOOLS],
               log=log, records=records), open(OUT, "w"), indent=1)
print("records:", len(records))
