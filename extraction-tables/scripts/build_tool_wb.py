"""Build one extraction workbook per tool in the format of niramai_extraction_table3.xlsx.

Inputs: the Niramai workbook (template), the cross-tool extraction table (library S01-S62),
a JSON spec per tool with new sources still to extract.
"""
import copy, json, re, sys
import openpyxl
from openpyxl.utils import get_column_letter as L

TEMPLATE, OLD, SPEC, OUTDIR = sys.argv[1:5]
spec = json.load(open(SPEC))
old = openpyxl.load_workbook(OLD, data_only=True)
lib = json.load(open(sys.argv[5]))

def snap(ws, rows, cols):
    return {(r, c): (copy.copy(ws.cell(r, c)._style)) for r in rows for c in cols}

def read_old_sources(sheet):
    ws = old[sheet]; rows = list(ws.iter_rows(values_only=True)); out = []
    for b in range(2, ws.max_column, 4):
        if not rows[0][b]: continue
        g = lambda i, off=0: rows[i][b + off] if b + off < len(rows[i]) else None
        out.append(dict(sno=rows[0][b], company=g(1), tool=g(2), type=g(3), title=g(4), authors=g(5), year=g(6), file=g(7), notes=g(8),
                        dp=[(g(i), g(i, 1)) for i in range(10, 20)], items=[(g(i), g(i, 1), g(i, 3)) for i in range(20, 49)]))
    return out

def build(tool):
    wb = openpyxl.load_workbook(TEMPLATE)
    ws = wb["Niramai (Thermalytix)"]; sc = wb["Scoring table"]
    sheet = tool["sheet"]
    # ---- styles from template block 1 ----
    ext_style = snap(ws, range(1, 55), range(1, 7)); heights = {r: ws.row_dimensions[r].height for r in range(1, 55)}
    sc_style = snap(sc, range(1, 42), range(1, 11)); sc_vals = {(r, c): sc.cell(r, c).value for r in range(1, 42) for c in range(1, 11)}
    for m in list(ws.merged_cells.ranges): ws.unmerge_cells(str(m))
    for m in list(sc.merged_cells.ranges): sc.unmerge_cells(str(m))
    ws.delete_cols(3, ws.max_column); sc.delete_cols(9, sc.max_column)
    ws.title = sheet
    srcs = tool["sources"]; n = len(srcs); qs = sheet.replace("'", "''")
    # ---- extraction sheet ----
    for k, s in enumerate(srcs):
        c0 = 3 + 4 * k
        for r in range(1, 55):
            for j in range(4):
                ws.cell(r, c0 + j)._style = copy.copy(ext_style[(r, 3 + j)])
        hdr = [k + 1, s["company"], s["tool"], s["type"], s["title"], s["authors"], s["year"], s["file"], s.get("same") or None, s["notes"]]
        for i, v in enumerate(hdr, 1):
            ws.cell(i, c0, v); ws.merge_cells(start_row=i, start_column=c0, end_row=i, end_column=c0 + 3)
        ws.cell(12, c0, "Value"); ws.cell(12, c0 + 1, "Verbatim supporting quote (page)"); ws.merge_cells(start_row=12, start_column=c0 + 1, end_row=12, end_column=c0 + 3)
        for i, (v, q) in enumerate(s["dp"]):
            ws.cell(13 + i, c0, v); ws.cell(13 + i, c0 + 1, q); ws.merge_cells(start_row=13 + i, start_column=c0 + 1, end_row=13 + i, end_column=c0 + 3)
        for j, h in enumerate(["Value", "Verbatim supporting quote (page)", "Final score", "Preliminary score (0/1/2)"]): ws.cell(25, c0 + j, h)
        for i, (v, q, p) in enumerate(s["items"]):
            ws.cell(26 + i, c0, v); ws.cell(26 + i, c0 + 1, q); ws.cell(26 + i, c0 + 2, None)
            ws.cell(26 + i, c0 + 3, int(p) if str(p).strip() in ("0", "1", "2") else (p or None))
        for j, w in enumerate((30, 55, 9, 12)): ws.column_dimensions[L(c0 + j)].width = w
    last_ext = L(max(2, 2 + 4 * n))
    for r in range(1, 11): ws.merge_cells(f"A{r}:B{r}")
    ws.merge_cells(f"A11:{last_ext}11"); ws.merge_cells(f"A24:{last_ext}24")
    ws.freeze_panes = "C2"
    # ---- scoring table ----
    lastc = L(8 + 2 * n) if n else "J"
    rng = f"$I$5:${lastc}$5"
    for (r, c), v in sc_vals.items():
        if c > 8: continue
        if isinstance(v, str):
            v = v.replace("$DD", f"${lastc}").replace("Niramai (Thermalytix)", qs)
            v = re.sub(r"over all \d+ sources", f"over all {n} sources", v).replace("(2 × 50)", f"(2 × {n})")
        sc.cell(r, c, v)
    for k, s in enumerate(srcs):
        cf, cp = 9 + 2 * k, 10 + 2 * k; ef, ep = L(3 + 4 * k + 2), L(3 + 4 * k + 3)
        for r in range(1, 42):
            sc.cell(r, cf)._style = copy.copy(sc_style[(r, 9)]); sc.cell(r, cp)._style = copy.copy(sc_style[(r, 10)])
        sc.cell(1, cf, k + 1); sc.cell(2, cf, s["title"]); sc.cell(3, cf, s["tool"]); sc.cell(4, cf, sheet)
        for r in range(1, 5): sc.merge_cells(start_row=r, start_column=cf, end_row=r, end_column=cp)
        sc.cell(5, cf, "Final score"); sc.cell(5, cp, "Preliminary score")
        for i in range(29):
            r, er = 6 + i, 26 + i
            sc.cell(r, cf, f"=IF('{qs}'!{ef}{er}=\"\",\"\",'{qs}'!{ef}{er})"); sc.cell(r, cp, f"='{qs}'!{ep}{er}")
        F, P = L(cf), L(cp)
        for col in (F, P):
            sc[f"{col}35"] = f"=SUM({col}6:{col}23)"; sc[f"{col}36"] = f"=SUM({col}24:{col}34)"; sc[f"{col}37"] = f"=SUM({col}6:{col}34)"; sc[f"{col}38"] = f"={col}37/58"
        sc[f"{F}39"] = f"=COUNT({F}6:{F}34)"
        sc.column_dimensions[F].width = 11; sc.column_dimensions[P].width = 11
    if not n:
        for r in range(6, 40):
            for c in range(3, 9): sc.cell(r, c).value = None
    for r in (1, 2, 3, 4, 35, 36, 37, 38, 39): sc.merge_cells(f"A{r}:B{r}")
    sc.merge_cells("C1:H4"); sc.merge_cells("A41:N41")
    # ---- duplicates / missing ----
    for name, rows in (("Duplicates removed", tool["dups"]), ("Missing full text", tool["missing"])):
        w = wb[name]; hdr = [c.value for c in w[1]]
        w.delete_rows(2, w.max_row)
        if name == "Duplicates removed": w["A1"] = "Source (original source number)"
        for row in rows:
            w.append(row)
            for c in w[w.max_row]: c.alignment = copy.copy(w["A1"].alignment); c.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical="top")
    # ---- sources still to extract ----
    if tool["to_add"]:
        t = wb.create_sheet("Sources to add", 1)
        H = ["Type", "Year", "Title", "Authors / sponsor", "Journal / registry", "ID", "Open access", "Link", "Decision", "Note", "Status"]
        t.append(H)
        for c in t[1]: c.font = openpyxl.styles.Font(bold=True); c.fill = openpyxl.styles.PatternFill("solid", fgColor="D9D9D9"); c.alignment = openpyxl.styles.Alignment(wrap_text=True)
        for a in tool["to_add"]:
            t.append([a["kind"], a["year"], a["title"], a["authors"], a["venue"], a["id"], a["oa"], a["link"], a["dec"], a["note"], "Pending full-text extraction"])
        for c, wdt in zip("ABCDEFGHIJK", (14, 7, 60, 28, 24, 26, 10, 36, 11, 45, 22)): t.column_dimensions[c].width = wdt
        for row in t.iter_rows(min_row=2):
            for c in row: c.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical="top")
        t.freeze_panes = "A2"; t.auto_filter.ref = t.dimensions
    # ---- read me ----
    rm = wb["Read me"]; rm.delete_rows(2, rm.max_row)
    for line in tool["readme"]: rm.append([line])
    for row in rm.iter_rows(min_row=2):
        for c in row: c.alignment = openpyxl.styles.Alignment(wrap_text=True, vertical="top")
    wb.save(f'{OUTDIR}/{tool["file"]}')
    return n

if __name__ == "__main__":
    for t in spec:
        if t.get("old_sheet"):
            t["sources"] = [s for s in read_old_sources(t["old_sheet"]) if s["sno"] not in t.get("drop", [])]
            # map old S-numbers to new S. No. in notes / same-study
            m = {s["sno"]: k + 1 for k, s in enumerate(t["sources"])}
            for s in t["sources"]:
                s["same"] = t.get("same", {}).get(s["sno"])
                for key in ("notes", "same"):
                    if s.get(key):
                        s[key] = re.sub(r"\bS(\d{2})\b", lambda mm: f"No. {m['S'+mm.group(1)]}" if 'S' + mm.group(1) in m else f"'{(lib.get('S'+mm.group(1)) or {}).get('title') or 'S'+mm.group(1)}'", s[key])
                s["orig"] = s["sno"]
                adds = {a["id"]: a for a in t["to_add"] if a["kind"] == "trial registration"}
                for i in lib.get(s["sno"], {}).get("ids", []):
                    if i in adds and lib[s["sno"]]["type"] != "trial_registration":
                        s["same"] = ((s["same"] + "; ") if s["same"] else "") + f"{i} (registration, in 'Sources to add')"
        else:
            t["sources"] = []
        print(t["file"], build(t))
