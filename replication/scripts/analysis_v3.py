import json, sys, statistics as st, collections, openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
B="."
sys.path.insert(0,f"{B}/scripts")
from elements import E
from india_relation import INDIA
R=json.load(open(f"{B}/element_coding_final.json"))
rows=json.load(open(f"{B}/corpus_in/rows.json")); h=rows[0]
name_of={r[h.index("tool_id")]+"_extraction_table.xlsx":r[h.index("tool_name")] for r in rows[1:]}
tools=json.load(open(f"{B}/results_v2/tools.json")); T={t["name"]:t for t in tools if t["n"]}
ITEMS=sorted({r["item"] for r in R},key=lambda s:[int(x) if x.isdigit() else x for x in s.split()[0].replace(".", " ").split()])
# ---- tool x item x element union
by=collections.defaultdict(list)
for r in R: by[(name_of[r["file"]],r["item"])].append(r)
def code(item): return item.split()[0]
EL={c:[(e[0],e[1]) for e in E[c][1]] for c in E}
tool_item={}
for (tool,item),rs in by.items():
    pres=set(i for r in rs for i in r["present_ids"]); app=set(i for r in rs for i in r["present_ids"]+r["missing_ids"])
    reported=any(r["final"]>0 for r in rs); best=max(r["final"] for r in rs)
    n_pres=len(pres) if pres else (1 if reported else 0)   # reported but element not identified counts as one element
    tool_item[(tool,item)]=dict(pres=pres,app=app,reported=reported,best=best,comp=(n_pres/len(app) if app else 0))
toolsN=sorted(T)
def iqr(xs):
    q=st.quantiles(xs,n=4,method="inclusive"); return f"{st.median(xs):g} ({q[0]:g}–{q[2]:g})"
def rk(v):
    s=sorted(range(len(v)),key=lambda i:v[i]); r=[0]*len(v); i=0
    while i<len(v):
        j=i
        while j+1<len(v) and v[s[j+1]]==v[s[i]]: j+=1
        for k in range(i,j+1): r[s[k]]=(i+j)/2+1
        i=j+1
    return r
def sp(a,b):
    ra,rb=rk(a),rk(b); ma,mb=st.mean(ra),st.mean(rb)
    return sum((x-ma)*(y-mb) for x,y in zip(ra,rb))/(sum((x-ma)**2 for x in ra)*sum((y-mb)**2 for y in rb))**.5
# per-tool measures
M={}
for t in toolsN:
    ti=[tool_item[(t,i)] for i in ITEMS if (t,i) in tool_item]
    rep=sum(x["reported"] for x in ti); p1=sum(tool_item[(t,i)]["reported"] for i in ITEMS[:18]); p2=rep-p1
    el_p=sum(len(x["pres"]) if x["pres"] else (1 if x["reported"] else 0) for x in ti); el_a=sum(len(x["app"]) for x in ti)
    per_src=[sum(r["final"] for r in R if name_of[r["file"]]==t and r["sno"]==s) for s in sorted({r["sno"] for r in R if name_of[r["file"]]==t})]
    M[t]=dict(rep=rep,p1=p1,p2=p2,comp=el_p/el_a,total=T[t]["total"],n=T[t]["n"],med_src=st.median(per_src),dev=T[t]["dev"])
wb=openpyxl.load_workbook(f"{B}/transparency_analysis_v2.xlsx")
H=Font(bold=True,color="FFFFFF"); HF=PatternFill("solid",fgColor="1F4E78"); W=Alignment(wrap_text=True,vertical="top"); BOLD=Font(bold=True)
def sheet(title,hdr,data,widths,idx):
    ws=wb.create_sheet(title,idx); ws.append(hdr)
    for c in ws[1]: c.font=H; c.fill=HF; c.alignment=W
    for d in data: ws.append(d)
    for row in ws.iter_rows(min_row=2):
        for c in row: c.alignment=W
    for i,w in enumerate(widths): ws.column_dimensions[openpyxl.utils.get_column_letter(i+1)].width=w
    ws.freeze_panes="B2"; return ws
N=len(toolsN)
# ---- A. primary measure: items reported
reps=[M[t]["rep"] for t in toolsN]; comps=[M[t]["comp"] for t in toolsN]; ns=[M[t]["n"] for t in toolsN]
key=[["PRIMARY MEASURE: items reported (STANDING Together items with any reporting, of 29; Laws et al. 'reported' rule)",""],
 ["Items reported per tool, median (IQR)",iqr(reps)],["Range",f"{min(reps)}–{max(reps)}"],
 ["Part 1 dataset documentation, items reported of 18, median (IQR)",iqr([M[t]["p1"] for t in toolsN])],
 ["Part 2 use of data, items reported of 11, median (IQR)",iqr([M[t]["p2"] for t in toolsN])],
 ["Tools reporting fewer than half of the items (< 15 of 29)",f"{sum(x<15 for x in reps)} of {N}"],["",""],
 ["COMPLETENESS (elements reported / applicable elements, all items; Laws Appendix 2 elements)",""],
 ["Completeness per tool, median (IQR)",f"{st.median(comps):.0%} ({st.quantiles(comps,n=4,method='inclusive')[0]:.0%}–{st.quantiles(comps,n=4,method='inclusive')[2]:.0%})"],
 ["Range",f"{min(comps):.0%}–{max(comps):.0%}"],["",""],
 ["SECONDARY: 0/1/2 total (of 58)",iqr([M[t]["total"] for t in toolsN])],["",""],
 ["WHO REPORTS (items reported of 29, median)",""]]
for d in ("global","indian"):
    xs=[M[t]["rep"] for t in toolsN if M[t]["dev"]==d]; key.append([f"{'Global' if d=='global' else 'Indian'} developers (n = {len(xs)})",iqr(xs)])
for lv in ("Routine use documented","Studied or trialled in India","Announced or claimed only","Indian product, no use found"):
    xs=[M[t]["rep"] for t in toolsN if INDIA[t][0]==lv]; key.append([f"Evidence of use: {lv[0].lower()+lv[1:]} (n = {len(xs)})",iqr(xs)])
key+=[["",""],["CAVEAT: NUMBER OF SOURCES",""],
 ["Spearman: number of public sources vs items reported",f"{sp(ns,reps):.2f}"],
 ["Spearman: number of public sources vs median score per source",f"{sp(ns,[M[t]['med_src'] for t in toolsN]):.2f}"],
 ["Median score per source (of 58), median across tools",iqr([M[t]['med_src'] for t in toolsN])],
 ["Note","Tool-level scores take the best source per item, so tools with many sources can report more items partly by chance; the per-source median is shown as a check."]]
ws=sheet("1 Primary measures",["Finding","Result"],key,[78,40],0)
for r in ws.iter_rows(min_row=2):
    if (r[0].value or "").isupper() or (r[0].value or "")[:8] in ("PRIMARY ","COMPLETE","SECONDAR","WHO REPO","CAVEAT: "): r[0].font=BOLD
# per tool table
data=[[t,INDIA[t][0],M[t]["dev"].title(),M[t]["n"],M[t]["rep"],M[t]["p1"],M[t]["p2"],round(M[t]["comp"],3),M[t]["total"],M[t]["med_src"]] for t in sorted(toolsN,key=lambda t:(-M[t]["rep"],-M[t]["comp"]))]
ws=sheet("2 Tools (primary)",["Tool","Evidence of use in India","Developer","Public sources","Items reported (of 29)","Part 1 reported (of 18)","Part 2 reported (of 11)","Completeness (elements reported / applicable)","Secondary: 0/1/2 total (of 58)","Median score per source (of 58)"],data,[42,24,10,9,10,10,10,14,12,12],1)
for row in ws.iter_rows(min_row=2): row[7].number_format="0%"
# ---- B. element reporting, Laws format
data=[]
for it in ITEMS:
    c=code(it)
    for eid,lab in EL[c]:
        app=[t for t in toolsN if (t,it) in tool_item and eid in tool_item[(t,it)]["app"]]
        k=sum(eid in tool_item[(t,it)]["pres"] for t in app)
        data.append([it,lab,len(app),k,(k/len(app)) if app else None])
ws=sheet("3 Elements (Laws format)",["STANDING Together item","Element (Codebook)","Tools where applicable","Tools reporting the element","% of tools"],data,[44,80,12,12,10],2)
for row in ws.iter_rows(min_row=2): row[4].number_format="0%"
# ---- C. item completeness and difficulty
src_c=collections.defaultdict(collections.Counter)
for r in R: src_c[r["item"]][r["final"]]+=1
data=[]
for it in ITEMS:
    c=code(it); vals=[tool_item[(t,it)] for t in toolsN if (t,it) in tool_item]
    data.append([it,len(EL[c]),sum(v["reported"] for v in vals)/N,st.mean(v["comp"] for v in vals),sum(v["best"]==2 for v in vals)/N,src_c[it][2],
                 "Never complete in any source" if src_c[it][2]==0 else ("Single element: only 0 or 2 possible" if len(EL[c])==1 else "")])
ws=sheet("4 Item difficulty",["Item","Elements in item","% of tools reporting the item","Mean completeness across tools","% of tools complete (2)","Sources scoring 2 (of 601)","Note"],data,[46,10,12,14,12,12,34],3)
for row in ws.iter_rows(min_row=2):
    for i in (2,3,4): row[i].number_format="0%"
# rename old sheets to follow
for old,new in (("1 Key findings","5 Other findings"),("2 Training vs evaluation","6 Training vs evaluation"),("3 STANDING Together items","7 Items 0-1-2 (secondary)"),("4 Tools","8 Tools and India link"),("5 Source types","9 Source types")):
    if old in wb.sheetnames: wb[old].title=new
rm=wb["Read me"]
for l in ["v3 structure: the PRIMARY measure is items reported (any reporting, Laws et al. rule); COMPLETENESS (elements reported / applicable elements, Laws Appendix 2) is shown per tool, per item and per element; the 0/1/2 total of 58 is SECONDARY because items differ in difficulty (sheet 4).",
          "Tool-level element reporting = union of elements reported across the tool's sources; an item reported in the extraction whose elements were not identified counts as one element.",
          "Codebook version 1.0, frozen 9 November 2026 (codebook_v1.0.xlsx)."]:
    rm.append([l]); rm.cell(rm.max_row,1).alignment=W
wb.save(f"{B}/transparency_analysis_v3.xlsx")
for k in key: print(k)
print(); [print([str(x)[:30] for x in d]) for d in data if d[6]]
