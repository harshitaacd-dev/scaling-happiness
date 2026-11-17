import json, re, collections, pandas as pd, numpy as np, statsmodels.formula.api as smf
B="."
R=json.load(open(f"{B}/element_coding_final.json")); S={(s["file"],s["sno"]):s for s in json.load(open(f"{B}/sources_v1.json"))}
rows=json.load(open(f"{B}/corpus_in/rows.json")); h=rows[0]; nm={r[h.index("tool_id")]+"_extraction_table.xlsx":r[h.index("tool_name")] for r in rows[1:]}
sc=collections.defaultdict(dict)
for r in R: sc[(r["file"],r["sno"])][r["item"].split()[0]]=r["final"]
nr=lambda v:(v or "").strip().lower().startswith("not reported")
TR=re.compile(r"(trained (on|using|with)|training (set|data|dataset|cohort|images|samples|videos)|(train|training)[ /-]*(validation|test)[ -]*(split|set)|development (set|dataset|cohort))",re.I)
def stype(t):
    t=str(t).lower()
    if t.startswith(("paper","preprint","conference","case report","book")): return "Study"
    if "trial registration" in t: return "Trial registration"
    if any(w in t for w in ("news","press","magazine")): return "News / press release"
    if t.startswith("web page"): return "Company / web page"
    return "Other"
out=[]
for k,s in S.items():
    q=" ".join(re.findall(r"“(.*?)”"," ".join(str(v[1]) for v in list(s["dp"].values())+[x[:2] for x in s["it"].values()]),re.S))
    acc=not (nr(s["dp"]["Sensitivity"][0]) and nr(s["dp"]["Specificity"][0]))
    out.append(dict(tool=nm[k[0]],stype=stype(s["type"]),
        accuracy=int(acc),                                   # favourable, checkable performance claim
        limitation=int(sc[k]["1.3a"]>0 or sc[k]["2.3a"]>0),  # unfavourable: limitations of data
        subgroup=int(sc[k]["2.2d"]>0),                       # performance by group (could reveal weakness)
        training=int(bool(TR.search(q)) and not nm[k[0]].startswith("Dognosis")),
        demog=int(not nr(s["dp"]["Population demographics reported (age, rural/urban, socioeconomic)"][0]))))
d=pd.DataFrame(out)
d["channel"]=np.where(d.stype.isin(["Company / web page","News / press release"]),"Developer-controlled (web, news)",np.where(d.stype=="Study","Peer-reviewed / study","Registration / other"))
tab=d.groupby("channel")[["accuracy","limitation","subgroup","training","demog"]].mean().mul(100).round(0)
tab["n"]=d.groupby("channel").size(); print(tab)
# among sources reporting accuracy: share also reporting limitations / subgroup / training
acc=d[d.accuracy==1]; t2=acc.groupby("channel")[["limitation","subgroup","training"]].mean().mul(100).round(0); t2["n reporting accuracy"]=acc.groupby("channel").size()
print("\nAmong sources that report accuracy:"); print(t2)
# test: gap (accuracy - limitation) larger in developer-controlled channels; long format, tool-clustered
L=pd.concat([d.assign(kind="accuracy",rep=d.accuracy),d.assign(kind="limitation",rep=d.limitation)])
L=L[L.channel!="Registration / other"]; L["dev"]=(L.channel.str.startswith("Developer")).astype(int); L["acc"]=(L.kind=="accuracy").astype(int)
m=smf.ols("rep ~ acc*dev",data=L).fit(cov_type="cluster",cov_kwds={"groups":pd.factorize(L.tool)[0]})
print("\nLinear probability model (accuracy vs limitation, developer-controlled vs study):")
print(m.params.round(3)); print(m.pvalues.round(3))
d.to_csv(f"{B}/strategic_sources.csv",index=False); tab.to_csv(f"{B}/strategic_tab.csv"); t2.to_csv(f"{B}/strategic_tab2.csv")
