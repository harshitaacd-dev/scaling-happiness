"""Second (verification) search. Complements search.py with:
 A. spelling/name variants (Europe PMC)
 B. Semantic Scholar (tool names), with slow retries
 C. citation chasing (backward + forward) via Europe PMC for every known paper
 D. topic search not tied to tool names: AI + breast/cervical screening + India
    (Europe PMC, ClinicalTrials.gov with India location, WHO ICTRP topic terms)
Output: raw JSON of all records, plus the query log.
"""
import json, re, sys, time, datetime, html
import requests
from bs4 import BeautifulSoup

OUT = sys.argv[1]; S1 = json.load(open(sys.argv[2])); LIB = json.load(open(sys.argv[3]))
TODAY = datetime.date.today().isoformat()
S = requests.Session(); S.headers["User-Agent"] = "dissertation-literature-search/1.0 (academic research)"
EPMC = "https://www.ebi.ac.uk/europepmc/webservices/rest"
log, records = [], []
TOOLRX = {t["id"]: t["rx"] for t in S1["tools"]}
TOOLRX.update({"T02": r"smart[ -]?scope|periwinkle tech", "T05": r"mobileodt|visual ?check|enhanced visual assessment|\bEVA (system|colposcope|device)",
               "T06": r"cervastra|aindra|intellistain", "T10": r"ibreastexam|ue life ?sciences|intelligent breast exam|\biBE\b"})

def get(url, tries=6, base=2, **kw):
    for i in range(tries):
        try:
            r = S.get(url, timeout=90, **kw)
            if r.status_code == 429 or r.status_code >= 500: time.sleep(base ** (i + 1)); continue
            return r
        except requests.RequestException: time.sleep(base ** (i + 1))
    return None

def logq(strategy, db, tid, q, hits, got, note=""):
    log.append(dict(date=TODAY, strategy=strategy, database=db, tool_id=tid, query=q, hits=hits, retrieved=got, note=note))
    print(f"{strategy[:12]:12s} {db:16s} {tid:4s} {q[:70]:70s} hits={hits} got={got} {note}", flush=True)

def epmc_rec(it, strategy, tid):
    urls = [u.get("url") for u in it.get("fullTextUrlList", {}).get("fullTextUrl", []) if u.get("availabilityCode") in ("OA", "F")]
    return dict(strategy=strategy, tool_id=tid, database="Europe PMC", kind="publication", pmid=it.get("pmid"), pmcid=it.get("pmcid"),
        doi=(it.get("doi") or "").lower(), title=it.get("title"), authors=it.get("authorString"), year=it.get("pubYear"),
        venue=it.get("journalInfo", {}).get("journal", {}).get("title") or it.get("source"), pubtype="; ".join(it.get("pubTypeList", {}).get("pubType", [])),
        abstract=it.get("abstractText") or "", open_access=it.get("isOpenAccess") == "Y",
        fulltext_url=urls[0] if urls else f'https://europepmc.org/article/{it.get("source")}/{it.get("id")}', epmc_id=f'{it.get("source")}/{it.get("id")}')

def epmc_search(strategy, tid, q, cap=2000):
    cursor, got, hits = "*", 0, None
    while True:
        r = get(f"{EPMC}/search", params=dict(query=q, format="json", resultType="core", pageSize=1000, cursorMark=cursor))
        if r is None or r.status_code != 200: logq(strategy, "Europe PMC", tid, q, hits, got, "ERROR"); return
        d = r.json(); hits = d.get("hitCount", 0)
        for it in d.get("resultList", {}).get("result", []):
            records.append(epmc_rec(it, strategy, tid)); got += 1
        nxt = d.get("nextCursorMark")
        if not nxt or nxt == cursor or got >= hits or got >= cap: break
        cursor = nxt
    logq(strategy, "Europe PMC", tid, q, hits, got)

# ---------- A. variants ----------
VARIANTS = [
    ("T01", '"Niramai Health Analytix"'), ("T01", '"Thermalytics" AND breast'), ("T01", '"thermal analytics" AND breast AND (India OR Indian)'),
    ("T02", '"SmartScope" AND (cervical OR cervix)'), ("T02", '"Smart-Scope" AND (cervical OR cervix)'), ("T02", '"Smart Scope CX"'),
    ("T04", '"automated visual evaluation" AND (India OR Indian)'), ("T04", '"AVE" AND cervical AND (India OR Indian) AND ("artificial intelligence" OR "deep learning")'),
    ("T05", '"EVA" AND colposcop* AND ("artificial intelligence" OR "deep learning" OR algorithm)'), ("T05", '"Visual Check" AND cervical'),
    ("T06", '"Aindra Systems"'), ("T06", '"IntelliStain"'), ("T06", '"autostainer" AND cervical AND (India OR Indian)'),
    ("T08", '"Telerad" AND mammography'), ("T09", '"C-MET" AND breast AND thermal'),
    ("T07", '"BPL" AND mammography AND ("artificial intelligence" OR "deep learning")'),
    ("T10", '"UE Life Sciences"'), ("T10", '"handheld breast scanner"'), ("T10", '"tactile" AND breast AND "iBE"'),
    ("T11", '"OptraSCAN" AND (cervical OR cervix OR pap OR cytology)'),
    ("T12", '"uPath" AND ("HER-2" OR ERBB2 OR "HER2/neu")'),
]
for tid, q in VARIANTS: epmc_search("A variants", tid, q)

# ---------- B. Semantic Scholar ----------
S2TERMS = [("T01", "Thermalytix"), ("T01", "Niramai"), ("T02", "Smart Scope cervical"), ("T02", "Periwinkle Technologies"), ("T04", "automated visual evaluation cervical"),
           ("T05", "MobileODT"), ("T05", "VisualCheck"), ("T06", "CervAstra"), ("T06", "Aindra"), ("T08", "MammoAssist"), ("T09", "Lord's Mark breast"),
           ("T10", "iBreastExam"), ("T11", "CytoSiA"), ("T11", "OptraSCAN"), ("T12", "uPath HER2"), ("T13", "MedXAI cervical")]
s2fail = 0
for tid, q in S2TERMS:
    r = None
    if s2fail >= 2:
        logq("B semantic", "Semantic Scholar", tid, q, None, 0, "SKIPPED (API unavailable on earlier queries)"); continue
    for i in range(5):
        r = get("https://api.semanticscholar.org/graph/v1/paper/search", tries=1, params=dict(query=q, limit=100,
                fields="title,abstract,year,venue,externalIds,authors,openAccessPdf,publicationTypes"))
        if r is not None and r.status_code == 200: break
        time.sleep(15 * (i + 1))
    if r is None or r.status_code != 200:
        s2fail += 1
        logq("B semantic", "Semantic Scholar", tid, q, None, 0, "UNAVAILABLE (rate-limited after retries)"); continue
    d = r.json(); kept = 0
    for it in d.get("data", []):
        ta = (it.get("title") or "") + " " + (it.get("abstract") or "")
        if not re.search(TOOLRX[tid], ta, re.I): continue
        ex = it.get("externalIds") or {}
        records.append(dict(strategy="B semantic", tool_id=tid, database="Semantic Scholar", kind="publication", pmid=ex.get("PubMed"), pmcid=ex.get("PubMedCentral"),
            doi=(ex.get("DOI") or "").lower(), title=it.get("title"), authors=", ".join(a["name"] for a in (it.get("authors") or [])[:6]), year=str(it.get("year") or ""),
            venue=it.get("venue"), pubtype="; ".join(it.get("publicationTypes") or []), abstract=it.get("abstract") or "",
            open_access=bool(it.get("openAccessPdf")), fulltext_url=(it.get("openAccessPdf") or {}).get("url") or f'https://www.semanticscholar.org/paper/{it.get("paperId")}'))
        kept += 1
    logq("B semantic", "Semantic Scholar", tid, q, d.get("total"), kept, "kept only records naming the tool in title/abstract")
    time.sleep(4)
logq("B openalex", "OpenAlex", "-", "(all tool terms)", None, 0, "UNAVAILABLE: daily quota exhausted on shared connection; covered by citation chasing")

# ---------- C. citation chasing ----------
seeds = {}
for o in S1["items"]:
    if o.get("decision", o.get("suggestion")) in ("Include", "Already in library") and o["kind"] == "publication" and o.get("pmid"):
        seeds[str(o["pmid"])] = o["tool_ids"]
# library papers: resolve by DOI/title through Europe PMC
for s, v in LIB.items():
    if v["type"] != "paper" or not v["title"]: continue
    r = get(f"{EPMC}/search", params=dict(query=f'TITLE:"{v["title"][:120]}"', format="json", pageSize=1))
    if r is not None and r.status_code == 200:
        res = r.json().get("resultList", {}).get("result", [])
        if res and res[0].get("pmid"): seeds.setdefault(res[0]["pmid"], [])
print("citation seeds:", len(seeds), flush=True)
allrx = "|".join(f"(?:{x})" for x in TOOLRX.values() if x)
nc = nr = kc = kr = 0
for pmid in seeds:
    for direction in ("citations", "references"):
        r = get(f"{EPMC}/MED/{pmid}/{direction}", params=dict(format="json", pageSize=1000))
        if r is None or r.status_code != 200: continue
        lst = r.json().get(f"{'citation' if direction=='citations' else 'reference'}List", {}).get("citation" if direction == "citations" else "reference", [])
        for it in lst:
            if direction == "citations": nc += 1
            else: nr += 1
            t = it.get("title") or ""
            m = [tid for tid, rx in TOOLRX.items() if rx and re.search(rx, t, re.I)]
            if not m: continue
            if direction == "citations": kc += 1
            else: kr += 1
            records.append(dict(strategy="C citations", tool_id=m[0], database=f"Europe PMC {direction}", kind="publication", pmid=it.get("id") if it.get("source") == "MED" else None,
                pmcid=None, doi=(it.get("doi") or "").lower(), title=t, authors=it.get("authorString"), year=str(it.get("pubYear") or ""),
                venue=it.get("journalAbbreviation") or it.get("source"), pubtype=it.get("citationType") or "", abstract="", open_access=None,
                fulltext_url=f'https://europepmc.org/article/{it.get("source")}/{it.get("id")}' if it.get("id") else "", via=f"PMID {pmid} ({direction})"))
        time.sleep(0.2)
logq("C citations", "Europe PMC", "all", f"forward citations of {len(seeds)} seed papers", nc, kc, "kept only titles naming a tool")
logq("C citations", "Europe PMC", "all", f"reference lists of {len(seeds)} seed papers", nr, kr, "kept only titles naming a tool")

# ---------- D. topic search ----------
TOPIC = ('TITLE_ABS:("artificial intelligence" OR "deep learning" OR "machine learning" OR "computer-aided" OR "computer aided" OR "automated" OR "neural network") '
         'AND TITLE_ABS:(breast OR cervical OR cervix OR mammograph* OR colposcop* OR thermograph*) AND TITLE_ABS:(cancer OR neoplasia OR precancer OR lesion*) '
         'AND TITLE_ABS:(screening OR detection OR triage) AND (TITLE_ABS:(India OR Indian) OR AFF:India) AND PUB_YEAR:[2015 TO 2026]')
epmc_search("D topic", "topic", TOPIC)

r = get("https://clinicaltrials.gov/api/v2/studies", params={"query.term": '("artificial intelligence" OR "deep learning" OR "machine learning" OR thermography OR "thermal imaging" OR "automated") AND (breast OR cervical OR cervix)',
        "query.locn": "India", "pageSize": 200, "countTotal": "true"})
if r is not None and r.status_code == 200:
    d = r.json()
    for s in d.get("studies", []):
        p = s["protocolSection"]; idm = p["identificationModule"]
        records.append(dict(strategy="D topic", tool_id="topic", database="ClinicalTrials.gov", kind="trial registration", trial_id=idm["nctId"],
            title=idm.get("officialTitle") or idm.get("briefTitle"), authors=p.get("sponsorCollaboratorsModule", {}).get("leadSponsor", {}).get("name"),
            year=(p.get("statusModule", {}).get("studyFirstSubmitDate") or "")[:4], venue="ClinicalTrials.gov", pubtype=p.get("statusModule", {}).get("overallStatus"),
            abstract=p.get("descriptionModule", {}).get("briefSummary", ""), open_access=True, fulltext_url=f'https://clinicaltrials.gov/study/{idm["nctId"]}'))
    logq("D topic", "ClinicalTrials.gov", "topic", "AI/thermography/automated AND breast/cervical; location India", d.get("totalCount"), len(d.get("studies", [])))

def ictrp(term):
    s = requests.Session(); s.headers["User-Agent"] = "Mozilla/5.0"
    soup = BeautifulSoup(s.get("https://trialsearch.who.int/", timeout=90).text, "html.parser")
    data = {i.get("name"): i.get("value", "") for i in soup.select("input[type=hidden]") if i.get("name")}
    data.update({"TextBox1": term, "Button1": "Search"})
    soup = BeautifulSoup(s.post("https://trialsearch.who.int/", data=data, timeout=180).text, "html.parser")
    m = re.search(r"(\d+) trials? found", soup.get_text(" ", strip=True)); hits = int(m.group(1)) if m else 0
    if hits > 10:
        sel = soup.find("select")
        if sel is not None:
            data = {i.get("name"): i.get("value", "") for i in soup.select("input[type=hidden]") if i.get("name")}
            data[sel.get("name")] = "100"; data["__EVENTTARGET"] = sel.get("name")
            soup = BeautifulSoup(s.post("https://trialsearch.who.int/", data=data, timeout=180).text, "html.parser")
    got = kept = 0
    for a in soup.find_all("a", href=re.compile(r"Trial2\.aspx\?TrialID=", re.I)):
        got += 1; tid = re.search(r"TrialID=([^&]+)", a["href"]).group(1).strip()
        if not tid.startswith("CTRI"): continue   # India only
        kept += 1
        tr = a.find_parent("tr"); cells = [c.get_text(" ", strip=True) for c in tr.find_all("td")] if tr else []
        date = next((c for c in cells if re.match(r"^\d{4}-\d{2}-\d{2}$", c)), "")
        records.append(dict(strategy="D topic", tool_id="topic", database="WHO ICTRP", kind="trial registration", trial_id=tid, title=a.get_text(" ", strip=True),
            authors="", year=date[:4], venue="CTRI", pubtype=cells[0] if cells else "", abstract="", open_access=True, fulltext_url="https://trialsearch.who.int/" + a["href"].lstrip("./")))
    logq("D topic", "WHO ICTRP", "topic", term, hits, kept, f"first {got} shown; kept CTRI (India) records only")
    time.sleep(2)

for term in ["artificial intelligence breast cancer", "artificial intelligence cervical cancer", "deep learning breast", "deep learning cervical",
             "machine learning breast cancer", "machine learning cervical cancer", "thermography breast", "thermal imaging breast",
             "automated cervical screening", "colposcopy artificial intelligence", "mammography artificial intelligence", "cytology artificial intelligence",
             "visual inspection acetic acid artificial intelligence", "breast cancer screening device", "cervical cancer screening device"]:
    try: ictrp(term)
    except Exception as e: logq("D topic", "WHO ICTRP", "topic", term, None, 0, f"ERROR {e}")

json.dump(dict(date=TODAY, log=log, records=records), open(OUT, "w"), indent=1)
print("records:", len(records))
