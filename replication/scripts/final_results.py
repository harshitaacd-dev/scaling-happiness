import openpyxl, statistics as st, collections
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.drawing.image import Image
B="."
src=openpyxl.load_workbook(f"{B}/transparency_analysis_v3.xlsx")
val=openpyxl.load_workbook(f"{B}/deliverables_v2/codebook_v1.0.xlsx")["Validation"]
def rows(name): ws=src[name]; return [list(r) for r in ws.iter_rows(min_row=2,values_only=True) if r[0] is not None]
def hdr(name): return [c.value for c in src[name][1]]
H=Font(bold=True,color="FFFFFF"); HF=PatternFill("solid",fgColor="1F4E78"); W=Alignment(wrap_text=True,vertical="top")
TITLE=Font(bold=True,size=13); NOTE=Font(italic=True,size=9,color="555555"); BOLD=Font(bold=True); LINE=Border(bottom=Side(style="thin",color="BFBFBF"))
out=openpyxl.Workbook(); contents=out.active; contents.title="Contents"
TOC=[]
def table(sheet, title, header, data, widths, note, pct_cols=(), freeze=True):
    ws=out.create_sheet(sheet); ws["A1"]=title; ws["A1"].font=TITLE
    ws["A2"]=note; ws["A2"].font=NOTE; ws["A2"].alignment=Alignment(wrap_text=True,vertical="top")
    ws.merge_cells(start_row=2,start_column=1,end_row=2,end_column=max(len(header),2)); ws.row_dimensions[2].height=max(30,15*(len(note)//150+1))
    for j,h in enumerate(header,1):
        c=ws.cell(4,j,h); c.font=H; c.fill=HF; c.alignment=W
    for i,r in enumerate(data,5):
        for j,v in enumerate(r,1):
            c=ws.cell(i,j,v); c.alignment=W; c.border=LINE
            if j in pct_cols and isinstance(v,(int,float)): c.number_format="0%"
            if isinstance(v,str) and v.isupper() and len(v)>3: c.font=BOLD
    for j,w in enumerate(widths,1): ws.column_dimensions[L(j)].width=w
    if freeze: ws.freeze_panes="B5"
    TOC.append((sheet,title)); return ws
P=hdr("2 Tools (primary)"); TP={r[0]:dict(zip(P,r)) for r in rows("2 Tools (primary)")}
I8=hdr("8 Tools and India link"); TI={r[0]:dict(zip(I8,r)) for r in rows("8 Tools and India link")}
names=list(TP); N=len(names)
q=lambda xs,f=lambda x:f"{x:g}":f"{f(st.median(xs))} ({f(st.quantiles(xs,n=4,method='inclusive')[0])}–{f(st.quantiles(xs,n=4,method='inclusive')[2])})"
pc=lambda x:f"{x:.0%}"
# ---- Table 1: flow
table("T1 Study flow","Table 1. Identification of tools and sources",["Stage","Number","Detail"],[
 ["TOOLS",None,None],
 ["Candidate tools identified",77,"Web research for 14 cancer types and 42 searches of the Clinical Trials Registry-India (via WHO ICTRP)"],
 ["Excluded",41,"Not AI, not a named product, not screening/early detection/diagnosis, no connection to India, or duplicates"],
 ["Tools included",36,"Connected to India: Indian developer, or used, trialled, sold, licensed or funded in India"],
 ["Tools with at least one public full text (analysed)",35,"Mukhia+ had no public full text"],
 ["SOURCES",None,None],
 ["Sources meeting the inclusion rule",820,"A study of the tool or a document by its company; found in Europe PMC, Crossref, ClinicalTrials.gov, WHO ICTRP and a web search"],
 ["Republished copies removed",31,"Same text as a source already included"],
 ["Sources without full text",213,"Paywalled or blocked papers and web pages; reported as a limitation"],
 ["Full texts obtained",607,None],
 ["Non-English sources excluded",6,"Russian (3), German, Polish, Indonesian"],
 ["Sources analysed (English full text)",601,"Scored on the 29 STANDING Together items"],
 ["Item scores",17429,"601 sources x 29 items"]],[52,10,90],"Counts from the final run of the audit pipeline.")
# ---- Table 2: characteristics
d=[[n,TI[n]["Company"],TI[n]["Developer"].title(),TI[n]["Cancer"],TI[n]["Relationship to India"],TI[n]["Evidence of use in India"],TI[n]["Public sources"],TI[n]["of which studies"]] for n in sorted(names,key=str.lower)]
dev=collections.Counter(TI[n]["Developer"] for n in names); ev=collections.Counter(TI[n]["Evidence of use in India"] for n in names)
table("T2 Tools","Table 2. Characteristics of the 35 tools analysed",["Tool","Company / developer","Developer","Cancer type(s)","Relationship to India","Evidence of use in India","Public sources (English full text)","of which studies"],d,[34,30,10,16,64,20,11,10],
 f"Developers: {dev['indian']} Indian, {dev['global']} global (multinational or international research). Evidence of use: "+", ".join(f"{k} {v}" for k,v in ev.items())+". Studies = papers, preprints, conference abstracts/papers, case reports, book chapters. Relationship to India from company, news and study sources; not checked against regulator records.")
# ---- Table 3: summary of measures
rep=[TP[n]["Items reported (of 29)"] for n in names]; comp=[TP[n]["Completeness (elements reported / applicable)"] for n in names]; tot=[TP[n]["Secondary: 0/1/2 total (of 58)"] for n in names]
table("T3 Summary","Table 3. Public transparency of the 35 tools: summary of measures",["Measure","Median (IQR)","Range","Interpretation"],[
 ["PRIMARY",None,None,None],
 ["Items reported (of 29)",q(rep),f"{min(rep)}–{max(rep)}","STANDING Together items with any public information (Laws et al. 2025 'reported' rule)"],
 ["   Part 1, dataset documentation (of 18)",q([TP[n]['Part 1 reported (of 18)'] for n in names]),None,None],
 ["   Part 2, use of data (of 11)",q([TP[n]['Part 2 reported (of 11)'] for n in names]),None,None],
 ["Tools reporting fewer than half of the items",f"{sum(x<15 for x in rep)} of {N}",None,None],
 ["COMPLETENESS",None,None,None],
 ["Elements reported / applicable elements",q(comp,pc),f"{pc(min(comp))}–{pc(max(comp))}","Share of the required details (Codebook v1.0, 110 elements) that are public"],
 ["SECONDARY",None,None,None],
 ["0/1/2 total (of 58), as scored",q(tot),f"{min(tot)}–{max(tot)}","Lower bound: complete reporting is understated (see Table 10)"],
 ["0/1/2 total, expected",q([TP[n]['0/1/2 total, expected (25% of 2-to-1 downgrades restored)'] for n in names]),None,"25% of downgrades from 2 to 1 restored, as found in the full-text check"],
 ["0/1/2 total, upper bound",q([TP[n]['0/1/2 total, upper bound (all downgrades restored)'] for n in names]),None,None],
 ["Median score per source (of 58)",q([TP[n]['Median score per source (of 58)'] for n in names]),None,"Typical single document; not affected by the number of sources"]],[44,18,12,80],
 "IQR = interquartile range. Tool score per item = highest score in any of the tool's public English sources. 0 = not reported, 1 = reported but not all applicable elements, 2 = all applicable elements.")
# ---- Table 4: per tool
d=[[n,TP[n]["Developer"],TP[n]["Evidence of use in India"],TP[n]["Public sources"],TP[n]["Items reported (of 29)"],TP[n]["Part 1 reported (of 18)"],TP[n]["Part 2 reported (of 11)"],TP[n]["Completeness (elements reported / applicable)"],TP[n]["Secondary: 0/1/2 total (of 58)"],TP[n]["0/1/2 total, upper bound (all downgrades restored)"],TP[n]["Median score per source (of 58)"]] for n in names]
table("T4 Tools scores","Table 4. Transparency per tool (sorted by items reported)",["Tool","Developer","Evidence of use in India","Public sources","Items reported (of 29)","Part 1 (of 18)","Part 2 (of 11)","Completeness","0/1/2 total (of 58)","0/1/2 total, upper bound","Median score per source"],d,[40,10,22,9,10,9,9,12,10,11,11],
 "Primary measure: items reported. Completeness: elements reported / applicable elements across all items. Upper bound: all downgrades from 2 to 1 restored.",pct_cols=(8,))
# ---- Table 5: per item
I4={r[0]:r for r in rows("4 Item difficulty")}; I7={r[1]:r for r in rows("7 Items 0-1-2 (secondary)")}
d=[]
for it,r in I4.items():
    part="Part 1" if it[0]=="1" else "Part 2"
    d.append([part,it,r[1],r[2],r[3],r[4],r[5],r[6] or ""])
table("T5 Items","Table 5. Reporting by STANDING Together item (35 tools)",["Part","Item","Elements in item","% of tools reporting the item","Mean completeness","% of tools complete (2)","Sources scoring 2 (of 601)","Note"],d,[8,58,10,12,12,12,12,30],
 "Items differ in difficulty: those with many elements rarely reach 'complete'. Ten items are never complete in any source; 1.1f has a single element (0 or 2 only).",pct_cols=(4,5,6))
# ---- Table 6: training vs evaluation summary + per tool
TV=rows("6 Training vs evaluation"); hv=hdr("6 Training vs evaluation")
tr=collections.Counter(r[3] for r in TV)
ev_cols=[("Study setting","Eval: setting"),("Sample size","Eval: sample size"),("Sensitivity or specificity","Eval: sensitivity/specificity"),("Population demographics","Eval: demographics"),("Reference standard","Eval: reference standard"),("Performance by subgroup","Eval: subgroup performance")]
d=[["EVALUATION DATA (tools with at least one public source reporting it)",None,None]]
for lab,col in ev_cols:
    k=sum(r[hv.index(col)]=="yes" for r in TV); d.append([lab,k,k/N])
d.append(["TRAINING DATA (best disclosure across all public sources, coded by hand)",None,None])
for lab in ["Nothing about training data","Explicitly withheld","Vague claim only","Size (and/or origin) stated, no breakdown","Training/test split described in a study"]:
    k=tr.get(lab,0); d.append([lab,k,k/N])
k=tr.get("Size (and/or origin) stated, no breakdown",0)+tr.get("Training/test split described in a study",0)
d+= [["At least the size of the training data stated",k,k/N],["Demographic breakdown of the training data in numbers",0,0.0]]
table("T6 Train vs eval","Table 6. Public disclosure of evaluation data and training data (35 tools)",["Element","Tools","% of tools"],d,[66,8,10],
 "Subgroup performance counted only where figures are reported for groups (element-based scoring). Training data coded from every source mentioning training; 81 of 601 sources (13%) mention the training data at all.",pct_cols=(3,))
d=[[r[0],r[1],r[2],r[3],r[4]]+r[5:12] for r in TV]
table("T7 Train vs eval tools","Table 7. Training and evaluation disclosure per tool",hv,d,[38,9,8,30,56,9,9,10,10,10,10,10],"Example / quote: what the public sources say about the training data (verbatim where quoted).")
# ---- Table 8: group comparisons
def grp(label,keyf,order):
    out=[[label.upper(),None,None,None,None]]
    for g in order:
        ns=[n for n in names if keyf(n)==g]
        if not ns: continue
        out.append([g,len(ns),q([TP[n]["Items reported (of 29)"] for n in ns]),q([TP[n]["Completeness (elements reported / applicable)"] for n in ns],pc),q([TP[n]["Secondary: 0/1/2 total (of 58)"] for n in ns])])
    return out
band=lambda n:"1–9 sources" if TP[n]["Public sources"]<10 else ("10–29 sources" if TP[n]["Public sources"]<30 else "30 or more sources")
d=grp("Developer",lambda n:TP[n]["Developer"],["Global","Indian"])+grp("Evidence of use in India",lambda n:TP[n]["Evidence of use in India"],["Routine use documented","Studied or trialled in India","Announced or claimed only","Indian product, no use found"])+\
  grp("Peer-reviewed or preprint study available",lambda n:"With a study" if (TI[n]["of which studies"] or 0)>0 else "Without a study",["With a study","Without a study"])+\
  grp("Number of public sources",band,["1–9 sources","10–29 sources","30 or more sources"])
table("T8 Groups","Table 8. Transparency by tool characteristics (median, IQR)",["Group","Tools","Items reported (of 29)","Completeness","0/1/2 total (of 58)"],d,[44,8,20,18,20],
 "Descriptive comparisons; groups are small and overlap (e.g. global developers more often have studies and many sources), so no significance tests are reported. Number of sources vs items reported: Spearman 0.63; vs median score per source: 0.31.")
# ---- Table 9: source types
table("T9 Source types","Table 9. What each type of public source discloses (601 sources)",hdr("9 Source types"),rows("9 Source types"),[34,9,14,14,16,14,16],
 "Share of sources of each type reporting the element; 'mention training data' from verbatim quotes (keyword search, checked).",freeze=False)
# ---- Table 10: validation
table("T10 Validation","Table 10. Reliability, validation and robustness",["Check","What was compared","Result"],[list(r) for r in val.iter_rows(min_row=2,values_only=True)],[30,60,90],
 "All checks were done by the analyst who wrote the codebook; an independent second coder is pending.",freeze=False)
# ---- Appendix: elements
d=[[r[0],r[1],r[2],r[3],r[4]] for r in rows("3 Elements (Laws format)")]
table("A1 Elements","Appendix Table A1. Reporting of each element (Codebook v1.0; Laws et al. 2025 format)",hdr("3 Elements (Laws format)"),d,[44,80,12,12,10],
 "Part 1 elements from Laws et al. (2025) Appendix 2; Part 2 elements from the STANDING Together recommendation wording. A tool reports an element if any of its sources does.",pct_cols=(5,))
# ---- Figure
fs=out.create_sheet("Figure 1"); fs["A1"]="Figure 1. Evaluation data vs training data: share of tools reporting each element (n = 35)"; fs["A1"].font=TITLE
img=Image(f"{B}/figures/training_vs_evaluation.png"); img.width, img.height = 900, 672; fs.add_image(img,"A3"); TOC.append(("Figure 1",fs["A1"].value))
# ---- contents
contents["A1"]="Final results: public transparency of the training and evaluation data of AI cancer screening tools connected to India"; contents["A1"].font=TITLE
contents["A2"]="35 tools, 601 public English sources, 29 STANDING Together items. Element-based scores (Codebook v1.0, frozen 9 November 2026)."; contents["A2"].font=NOTE
contents.append([]); contents.append(["Sheet","Content"])
for c in contents[4]: c.font=H; c.fill=HF
for s,t in TOC: contents.append([s,t])
contents.column_dimensions["A"].width=22; contents.column_dimensions["B"].width=100
out.save(f"{B}/final_results.xlsx"); print("sheets:",out.sheetnames)
