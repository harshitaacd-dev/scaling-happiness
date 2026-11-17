import json, sys, collections
sys.path.insert(0, "./scripts")
from elements import E, code_source
B="."
S=json.load(open(f"{B}/sources_v1.json"))
rows=[]; trans=collections.Counter(); byitem=collections.defaultdict(collections.Counter)
for s in S:
    for code in E:
        k=next(x for x in s["it"] if x.startswith(code)); old=s["it"][k][2]
        sc,pr,mi,n=code_source(s,code)
        rows.append(dict(file=s["file"],sheet=s["sheet"],sno=s["sno"],col=s["col"],type=s["type"],title=s["title"],item=k,old=old,new=sc,
                         present=[l for _,l in pr],missing=[l for _,l in mi],present_ids=[i for i,_ in pr],missing_ids=[i for i,_ in mi],applicable=n))
        trans[(old,sc)]+=1; byitem[code][(old,sc)]+=1
json.dump(rows,open(f"{B}/element_coding.json","w"),ensure_ascii=False)
print("old -> new transition (all", len(rows),"item scores)")
for o in (0,1,2): print(f"  old {o}: ", {n:trans[(o,n)] for n in (0,1,2)})
print("\nper item  old dist -> new dist   (0/1/2)")
for code,c in byitem.items():
    od=[sum(v for (o,n),v in c.items() if o==x) for x in (0,1,2)]; nd=[sum(v for (o,n),v in c.items() if n==x) for x in (0,1,2)]
    print(f"  {code}  {od} -> {nd}   0->+ {sum(v for (o,n),v in c.items() if o==0 and n>0)}  +->0 {sum(v for (o,n),v in c.items() if o>0 and n==0)}")
