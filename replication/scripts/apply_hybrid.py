import json, re, os, glob, shutil, collections, openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
B="."
R=json.load(open(f"{B}/element_coding.json")); S={(s["file"],s["sno"]):s for s in json.load(open(f"{B}/sources_v1.json"))}
CLAIM=re.compile(r"(context only|general context|context\b|claim|without (figures|numbers|data|supporting)|no (data|figures)|unsupported|marketing)",re.I)
for r in R:
    v=S[(r["file"],r["sno"])]["it"][r["item"]][0]
    if r["old"]>0 and r["new"]==0:
        r["final"]=0 if CLAIM.search(v) else 1
        r["rule"]="reported in extraction (verbatim quote); elements not detected" if r["final"]==1 else "context or claim only (no data)"
    else:
        r["final"]=r["new"]; r["rule"]="element count"
json.dump(R,open(f"{B}/element_coding_final.json","w"),ensure_ascii=False)
t=collections.Counter((r["old"],r["final"]) for r in R)
print("current -> final:"); [print(f"  {o}: ",{n:t[(o,n)] for n in (0,1,2)}) for o in (0,1,2)]
print("final distribution:",collections.Counter(r["final"] for r in R))
# ---- write workbooks
SRC=f"{B}/final_en/output"; OUT=f"{B}/final_v2/output"; os.makedirs(OUT,exist_ok=True)
by=collections.defaultdict(list)
for r in R: by[r["file"]].append(r)
H=Font(bold=True,color="FFFFFF"); HF=PatternFill("solid",fgColor="1F4E78"); W=Alignment(wrap_text=True,vertical="top")
KNOWN={"Master scores","Scoring table","Duplicates removed","Missing full text","Read me","Excluded (not English)","Sources to add","Element coding"}
for f in sorted(glob.glob(f"{SRC}/*_extraction_table.xlsx")):
    name=os.path.basename(f); wb=openpyxl.load_workbook(f); ws=next(w for w in wb.worksheets if w.title not in KNOWN)
    rows=sorted(by.get(name,[]),key=lambda r:(r["sno"],r["item"]))
    for r in rows:
        row=26+[k for k in S[(r["file"],r["sno"])]["it"]].index(r["item"])
        assert ws.cell(row,r["col"]+2).value==r["old"]
        ws.cell(row,r["col"]+2).value=r["final"]
    if "Element coding" in wb.sheetnames: del wb["Element coding"]
    ec=wb.create_sheet("Element coding")
    ec.append(["S. No.","Source type","STANDING Together item","Final score","Elements reported","Elements not reported (what a score of 2 would add)","Applicable elements","Basis of score"])
    for c in ec[1]: c.font=H; c.fill=HF; c.alignment=W
    for r in rows:
        ec.append([r["sno"],r["type"],r["item"],r["final"],"; ".join(r["present"]) or "None",
                   ("; ".join(r["missing"]) if r["final"]>0 else "Not reported (item absent from this source)") if r["missing"] else "None (all applicable elements reported)",
                   r["applicable"],r["rule"]])
    for row in ec.iter_rows(min_row=2):
        for c in row: c.alignment=W
    for col,w in zip("ABCDEFGH",(7,16,40,8,60,70,10,30)): ec.column_dimensions[col].width=w
    ec.freeze_panes="D2"; ec.auto_filter.ref=ec.dimensions
    rm=wb["Read me"]
    for l in ["SCORING (final): 0 = not reported; 1 = reported, but not all applicable elements; 2 = all applicable elements reported. Elements per item follow Laws et al. (2025) Appendix 2 (Part 1) and the STANDING Together recommendation wording (Part 2); see the 'Element coding' sheet and the codebook in master_corpus.xlsx.",
              "The 'Final score' column holds these element-based scores; the 'Preliminary score' column keeps the original extraction score for reference."]:
        rm.append([l]); rm.cell(rm.max_row,1).alignment=W
    wb.save(f"{OUT}/{name}")
print("workbooks written:",len(glob.glob(f"{OUT}/*.xlsx")))
