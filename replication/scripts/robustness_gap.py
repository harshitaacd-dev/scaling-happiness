import json, math, collections, statistics as st, random
import numpy as np, pandas as pd, statsmodels.formula.api as smf, openpyxl
B="."
wb=openpyxl.load_workbook(f"{B}/final_results.xlsx")
T4={r[0]:r for r in wb["T4 Tools scores"].iter_rows(min_row=5,values_only=True) if r[0]}
T2={r[0]:r for r in wb["T2 Tools"].iter_rows(min_row=5,values_only=True) if r[0]}
tool=pd.DataFrame([dict(tool=n,glob=int(T4[n][1]=="Global"),n_src=T4[n][3],study=int((T2[n][7] or 0)>0),n_study=T2[n][7] or 0,
                         items=T4[n][4],comp=T4[n][7],total=T4[n][8],routine=int(T4[n][2]=="Routine use documented")) for n in T4])
tool["ln_src"]=np.log(tool.n_src)
print("TOOL LEVEL (n=35)")
print(pd.crosstab(tool.glob,tool.study,margins=True))
print("global tools: sources", sorted(tool[tool.glob==1].n_src.tolist()), "| Indian with study:",int(((tool.glob==0)&(tool.study==1)).sum()))
# stratified medians
for lab,sub in [("with a study",tool[tool.study==1]),("10+ sources",tool[tool.n_src>=10]),("with study and 10+ sources",tool[(tool.study==1)&(tool.n_src>=10)])]:
    g=sub[sub.glob==1]; i=sub[sub.glob==0]
    print(f"  {lab}: global n={len(g)} items {g['items'].median():g} comp {g.comp.median():.0%} | Indian n={len(i)} items {i['items'].median():g} comp {i.comp.median():.0%}")
res={}
for y in ["items","comp","total"]:
    for spec in [f"{y} ~ glob", f"{y} ~ glob + ln_src", f"{y} ~ glob + ln_src + study"]:
        m=smf.ols(spec,data=tool).fit(cov_type="HC3")
        res[spec]=(m.params["glob"],m.bse["glob"],m.pvalues["glob"],m.rsquared)
        print(f"  {spec:32s} glob={m.params['glob']:6.2f} (SE {m.bse['glob']:.2f}, p={m.pvalues['glob']:.3f})  R2={m.rsquared:.2f}"+("" if "+" not in spec else f"  ln_src={m.params['ln_src']:.2f} (p={m.pvalues['ln_src']:.3f})"+(f" study={m.params['study']:.2f} (p={m.pvalues['study']:.3f})" if "study" in spec else "")))
# permutation test for glob coefficient in full model (items)
m0=smf.ols("items ~ glob + ln_src + study",data=tool).fit(); obs=m0.params["glob"]; rng=np.random.default_rng(1); cnt=0; R=5000
for _ in range(R):
    d=tool.copy(); d["glob"]=rng.permutation(d.glob.values)
    if abs(smf.ols("items ~ glob + ln_src + study",data=d).fit().params["glob"])>=abs(obs): cnt+=1
print(f"  permutation p (items, full model): {(cnt+1)/(R+1):.3f}")
# ---------------- SOURCE LEVEL
R_=json.load(open(f"{B}/element_coding_final.json")); S={(s["file"],s["sno"]):s for s in json.load(open(f"{B}/sources_v1.json"))}
rows=json.load(open(f"{B}/corpus_in/rows.json")); h=rows[0]; nm={r[h.index("tool_id")]+"_extraction_table.xlsx":r[h.index("tool_name")] for r in rows[1:]}
agg=collections.defaultdict(lambda:dict(score=0,items=0))
for r in R_:
    k=(r["file"],r["sno"]); agg[k]["score"]+=r["final"]; agg[k]["items"]+=int(r["final"]>0)
def stype(t):
    t=str(t).lower()
    if t.startswith(("paper","preprint","conference","case report","book")): return "study"
    if "trial registration" in t: return "registration"
    if any(w in t for w in ("news","press","magazine")): return "news"
    if t.startswith("web page"): return "web"
    return "other"
src=pd.DataFrame([dict(tool=nm[k[0]],score=v["score"],items=v["items"],stype=stype(S[k]["type"])) for k,v in agg.items()])
src=src.merge(tool[["tool","glob","ln_src","study"]],on="tool")
print("\nSOURCE LEVEL (n=%d sources)"%len(src))
print(src.groupby(["stype","glob"]).score.agg(["count","mean","median"]).round(1))
for spec in ["score ~ glob","score ~ glob + C(stype)","score ~ glob + C(stype) + ln_src","items ~ glob + C(stype) + ln_src"]:
    m=smf.ols(spec,data=src).fit(cov_type="cluster",cov_kwds={"groups":pd.factorize(src.tool)[0]})
    res[spec]=(m.params["glob"],m.bse["glob"],m.pvalues["glob"],m.rsquared)
    print(f"  {spec:36s} glob={m.params['glob']:5.2f} (cluster SE {m.bse['glob']:.2f}, p={m.pvalues['glob']:.3f})  R2={m.rsquared:.2f}")
json.dump({k:list(v) for k,v in res.items()},open(f"{B}/gap_tests.json","w"))
tool.to_csv(f"{B}/tool_level.csv",index=False); src.to_csv(f"{B}/source_level.csv",index=False)
