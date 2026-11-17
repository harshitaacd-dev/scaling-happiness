"""Appendix B: one table per tool with the final STANDING Together score of every source on every item.
Reads the frozen source-level scores and checks that each tool's best scores equal Table B.1 (rev/appendix_matrix.md)."""
import openpyxl, re, sys, collections, difflib
B = "."
paper = open(f"{B}/rev/full.md", encoding="utf-8").read()
matrix = open(f"{B}/rev/appendix_matrix.md", encoding="utf-8").read()
paper_m = paper + "\n<!--MATRIX-->\n" + matrix

def table_rows(start, end):
    seg = paper_m[paper_m.index(start):paper_m.index(end)]
    return [[c.strip() for c in l.strip().strip('|').split('|')] for l in seg.split('\n')
            if l.startswith('|') and not l.startswith('|:')]

t42 = table_rows('<!--LANDSCAPE_START-->', 'Table: Table 4.2')
t43 = table_rows('<!--MATRIX-->', 'Table: Table B.1')
items = t43[0][1:30]
T42 = {r[0]: dict(zip(t42[0], r)) for r in t42[1:] if not r[0].startswith('**')}
T43 = {r[0]: ''.join(x if x in '012' else '0' for x in r[1:30]) for r in t43[1:] if not r[0].startswith('**')}
order = list(T42)

wb = openpyxl.load_workbook(f"{B}/deliverables_v2/standing_together_scores_by_source.xlsx", read_only=True, data_only=True)
rows = [r for r in wb['Master (all sources)'].iter_rows(min_row=4, values_only=True) if r[0]]
mc = {r[0]: r for r in openpyxl.load_workbook(f"{B}/deliverables_v2/master_corpus.xlsx", read_only=True, data_only=True)['Master corpus'].iter_rows(min_row=4, values_only=True) if r[0] and r[9]}

by = collections.defaultdict(list)
for r in rows: by[r[0]].append(r)

def best(rs): return ''.join(str(max(int(r[7 + i] or 0) for r in rs)) for i in range(29))
# map long sheet names to the short names used in Tables 4.2 and 4.3 (via identical score vectors, then name)
inv = collections.defaultdict(list)
for k, v in T43.items(): inv[v].append(k)
name = {}
for k, rs in by.items():
    c = inv.get(best(rs), [])
    name[k] = c[0] if len(c) == 1 else (k if k in c else difflib.get_close_matches(k, c, 1, 0)[0])
print(set(name.values())^set(order), len(set(name.values())));assert sorted(name.values()) == sorted(order), "tool mapping failed"
for k, rs in by.items(): assert best(rs) == T43[name[k]], f"best scores differ from Table B.1: {k}"
assert len(rows) == 601

def stype(t):
    t = str(t).lower()
    if t.startswith(("paper", "preprint", "conference", "case report", "book")): return "Study"
    if "trial registration" in t: return "Registration"
    if any(w in t for w in ("news", "press", "magazine")): return "News"
    if t.startswith("web page"): return "Web page"
    return "Other"
cnt = collections.Counter(stype(r[2]) for r in rows)
assert cnt == {"Web page": 181, "Study": 171, "News": 127, "Registration": 114, "Other": 8}, cnt

def yr(y):
    m = re.search(r'(19|20)\d\d', str(y or ''))
    return m.group(0) if m else 'n.d.'

def esc(s):
    s = re.sub(r'\s+', ' ', str(s or '')).strip()
    return re.sub(r'([\\*_\[\]<>|#`$@^~])', r'\\\1', s)

long = {v: k for k, v in name.items()}
out = ["# Appendix B: Scores by tool and source", "",
       "This appendix reports each tool's final score on each of the 29 STANDING Together items (Section B.1, Table B.1) and, for each tool, "
       "the final score of every public source behind it (Sections B.2 to B.36). Scores are 0 = not reported, 1 = partially reported and 2 = completely reported "
       "(codebook in Appendix A). The last row of each source table is the tool's score, the highest score of any of its sources on each item, as in Table B.1. "
       "Tools appear in the order of Table 4.2. "
       "Below each table, a key lists the sources by number, with their type, year, title and location. Sources marked as local PDF files "
       "were obtained manually (for example, through the university library) and are not redistributed. The source-level scores are also available in the public repository; quotations from paywalled sources are withheld.", "", "```{=openxml}", "<!--LANDSCAPE_START-->", "```", "",
       "## B.1 Scores of each tool on each item", "", matrix.strip(), "",
       '```{=openxml}', '<w:p><w:r><w:br w:type="page"/></w:r></w:p>', '```', ""]
for n, short in enumerate(order, 2):
    k = long[short]; rs = sorted(by[k], key=lambda r: int(r[1]))
    p = T42[short]; c = difflib.get_close_matches(k, list(mc), 1, 0.3)[0]
    out += [f"## B.{n} {esc(short)}", "",
            f"*Developer:* {esc(mc[c][1])} ({p['Developer']}). *Cancer:* {esc(p['Cancer'])}. *Use in India:* {esc(p['Use in India'])}. "
            f"*Public sources:* {p['Sources (studies)'].replace('(', '(studies: ')}. *Items reported:* {p['Items (of 29)']} of 29; *total score:* {p['Total (of 58)']} of 58.", ""]
    hdr = ["No.", "Type", "Year"] + items + ["Total"]
    out += ["| " + " | ".join(hdr) + " |", "|" + "|".join([":--", ":----", ":--"] + ["--:"] * 29 + ["--:"]) + "|"]
    for r in rs:
        v = [int(x or 0) for x in r[7:36]]
        out.append("| " + " | ".join([str(r[1]), stype(r[2]), yr(r[3])] + [str(x) for x in v] + [str(sum(v))]) + " |")
    b = [int(x) for x in best(rs)]
    out.append("| " + " | ".join(["**Tool**", "", ""] + [f"**{x}**" for x in b] + [f"**{sum(b)}**"]) + " |")
    out += ["", f"Table: Table B.{n}: Scores by source, {esc(short)}", "", '::: {custom-style="Source Key"}']
    for r in rs:
        link = str(r[6] or "")
        loc = f"<{link}>" if link.startswith("http") else "Local PDF copy (obtained manually, not redistributed)"
        y_ = yr(r[3]); out.append(f"**{r[1]}.** {stype(r[2])}, {y_}{' ' if y_.endswith('.') else '. '}{esc(r[4])}. {loc}")
        out.append("")
    out += [":::", ""]
out += ["```{=openxml}", "<!--LANDSCAPE_END-->", "```", ""]
open(f"{B}/rev/appendix_b.md", "w", encoding="utf-8").write("\n".join(out))
print("tools", len(order), "sources", len(rows), "checks passed")
