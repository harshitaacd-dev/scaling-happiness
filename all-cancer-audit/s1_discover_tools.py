"""Step 1: discover AI cancer screening tools in India.

(a) Claude web search, one research run per cancer type.
(b) WHO ICTRP (covers CTRI) topic searches, keeping Indian (CTRI) registrations.
Output: data/discovery_web.json, data/discovery_ctri.json
Re-running skips cancer types already done; delete the JSON files to start again.
"""
import re
import time

import requests
from bs4 import BeautifulSoup

from common import load, save, web_research

CANCERS = [
    # (cancer, sex group used for the comparison)
    ("breast cancer", "women-specific"), ("cervical cancer", "women-specific"),
    ("ovarian cancer", "women-specific"), ("endometrial or uterine cancer", "women-specific"),
    ("prostate cancer", "men-specific"),
    ("oral cancer", "all"), ("lung cancer", "all"), ("colorectal cancer", "all"),
    ("stomach, oesophageal or gastrointestinal cancers (endoscopy)", "all"), ("liver cancer", "all"),
    ("skin cancer", "all"), ("head and neck or thyroid cancer", "all"), ("blood cancers (leukaemia, lymphoma)", "all"),
    ("multi-cancer early detection (blood, breath or urine tests)", "all"),
]

PROMPT = """Find every AI-powered tool used for screening or early detection of {cancer} in India.

Include a tool if it uses AI or machine learning, is a named product or a named programme, and has been used, trialled, piloted,
licensed or approved in India (CDSCO licence, CTRI registration, state or national programme, hospital deployment,
peer-reviewed study on Indian patients). Indian and foreign companies both count if the tool is used in India.
Also list tools that only work after diagnosis (grading, prognosis, treatment choice) for this cancer, marked as such.
Exclude pure academic models that were never named, deployed or trialled.

Search widely: company and startup sites, news, CDSCO and CTRI, IndiaAI, NITI Aayog Frontier Tech, ICMR, BIRAC,
the IndiaAI-National Cancer Grid CATCH grant, state government programmes, PubMed, and conference abstracts.

For each tool give: tool name; company or developer; country of the company; what it does (modality);
screening or after-diagnosis; evidence of use in India (with the source URL); regulatory status if found;
and how confident you are that it is real and used in India. Be exhaustive; list uncertain candidates separately."""

TERMS = ["artificial intelligence", "deep learning", "machine learning"]


def ictrp(term):
    s = requests.Session(); s.headers["User-Agent"] = "Mozilla/5.0"
    soup = BeautifulSoup(s.get("https://trialsearch.who.int/", timeout=90).text, "html.parser")
    data = {i.get("name"): i.get("value", "") for i in soup.select("input[type=hidden]") if i.get("name")}
    data.update({"TextBox1": term, "Button1": "Search"})
    soup = BeautifulSoup(s.post("https://trialsearch.who.int/", data=data, timeout=180).text, "html.parser")
    m = re.search(r"(\d+) trials? found", soup.get_text(" ", strip=True))
    if m and int(m.group(1)) > 10 and soup.find("select") is not None:
        sel = soup.find("select")
        data = {i.get("name"): i.get("value", "") for i in soup.select("input[type=hidden]") if i.get("name")}
        data[sel.get("name")] = "100"; data["__EVENTTARGET"] = sel.get("name")
        soup = BeautifulSoup(s.post("https://trialsearch.who.int/", data=data, timeout=180).text, "html.parser")
    out = []
    for a in soup.find_all("a", href=re.compile(r"Trial2\.aspx\?TrialID=", re.I)):
        tid = re.search(r"TrialID=([^&]+)", a["href"]).group(1).strip()
        if tid.startswith("CTRI"):
            out.append(dict(trial_id=tid, title=a.get_text(" ", strip=True),
                            url="https://trialsearch.who.int/" + a["href"].lstrip("./")))
    return out


if __name__ == "__main__":
    web = load("discovery_web.json", {})
    for cancer, group in CANCERS:
        if cancer in web:
            continue
        print("web research:", cancer, flush=True)
        web[cancer] = dict(sex_group=group, notes=web_research(PROMPT.format(cancer=cancer)))
        save("discovery_web.json", web)

    ctri = load("discovery_ctri.json", {})
    for cancer, _ in CANCERS:
        key = cancer.split(" (")[0].split(",")[0]
        for t in TERMS:
            q = f"{t} {key}"
            if q in ctri:
                continue
            try:
                ctri[q] = ictrp(q)
            except Exception as e:  # registry hiccups should not stop the run
                ctri[q] = []; print("ICTRP error", q, e)
            print(f"CTRI {q}: {len(ctri[q])}", flush=True)
            save("discovery_ctri.json", ctri)
            time.sleep(2)
    print("done")
