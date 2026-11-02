# Collect titles + trial IDs of the existing library (S01-S62) from the extraction workbook
import sys, openpyxl, re, json
wb = openpyxl.load_workbook(sys.argv[1], data_only=True)
lib={}
for ws in wb.worksheets:
    if ws.title in ("Read me",): continue
    rows=list(ws.iter_rows(values_only=True))
    if ws.title=="Missing full text":
        for r in rows[1:]:
            if r[0]: lib[r[0]]={"title":r[3],"tool":r[1],"type":r[2],"text":" ".join(str(c) for c in r if c)}
        continue
    for b in range(2, ws.max_column, 4):
        s=rows[0][b]
        if not s: continue
        txt=" ".join(str(r[b]) for r in rows if r[b]) + " " + " ".join(str(r[b+1]) for r in rows if len(r)>b+1 and r[b+1])
        lib[s]={"title":rows[4][b],"tool":ws.title,"type":rows[3][b],"text":txt[:20000]}
for s,v in lib.items():
    v["ids"]=sorted(set(re.findall(r"(CTRI/\d{4}/\d{2,3}/\d{6}|NCT\d{8}|10\.\d{4,9}/[^\s\"”;,)]+|PMC\d+)", v["text"].replace("0 10 115","010115"))))
    del v["text"]
json.dump(lib, open(sys.argv[2],"w"), indent=1)
print(len(lib)); [print(k, v["tool"][:25], (v["title"] or "")[:60], v["ids"][:4]) for k,v in sorted(lib.items())]
