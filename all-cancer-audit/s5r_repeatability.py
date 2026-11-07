"""Repeatability check for step 5: extract a sample of sources a second time and compare the scores.

    python s5r_repeatability.py              # 6 sources (2 papers, 2 registrations, 2 web pages where available)
    python s5r_repeatability.py --n 10

The second extraction goes to data/extractions_repeat/ and never replaces the first. Reports, over all 29 items:
exact agreement, agreement within one point, Cohen's kappa, and the difference in source totals. Costs about as much
as extracting the sampled sources once. Report the result in your methods (test-retest reliability of the
preliminary scores).
"""
import argparse
import json
import random
from collections import Counter

import s5_extract as s5
from common import DATA, load


def kappa(pairs):
    n = len(pairs)
    po = sum(a == b for a, b in pairs) / n
    ca, cb = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--n", type=int, default=6); ap.add_argument("--seed", type=int, default=1)
    args = ap.parse_args()
    import csv
    names = {t["tool_id"]: t["tool_name"] for t in csv.DictReader(open(DATA / "corpus.csv", encoding="utf-8-sig"))}
    sources = load("sources.json")
    done = [(tid, r) for tid, recs in sources.items() for r in recs
            if r.get("source_id") and (s5.EXT / f"{r['source_id']}.json").exists()]
    random.seed(args.seed)
    by_kind = {}
    for tid, r in done:
        by_kind.setdefault(r["kind"], []).append((tid, r))
    sample, per = [], max(1, args.n // 3)
    for kind in ("publication", "trial registration", "web page"):
        pool = by_kind.get(kind, [])
        sample += random.sample(pool, min(per, len(pool)))
    rest = [x for x in done if x not in sample]
    sample += random.sample(rest, min(args.n - len(sample), len(rest)))
    print(f"re-extracting {len(sample)} sources...", flush=True)

    first_dir, repeat_dir = s5.EXT, DATA / "extractions_repeat"
    repeat_dir.mkdir(exist_ok=True)
    s5.EXT = repeat_dir  # second extraction goes here
    pairs, rows = [], []
    for tid, r in sample:
        res = s5._safe(names.get(tid, tid), r)
        a = json.loads((first_dir / f"{r['source_id']}.json").read_text())["_rendered"]["items"]
        p = repeat_dir / f"{r['source_id']}.json"
        if not p.exists():
            print(f"  {r['source_id']}: {res}"); continue
        b = json.loads(p.read_text())["_rendered"]["items"]
        sa, sb = [x[2] for x in a], [x[2] for x in b]
        pairs += list(zip(sa, sb))
        rows.append((r["source_id"], r["kind"], sum(sa), sum(sb), sum(x == y for x, y in zip(sa, sb))))
        print(f"  {r['source_id'][:44]:44s} {r['kind'][:18]:18s} first {sum(sa):2d}/58  second {sum(sb):2d}/58  "
              f"same score on {sum(x == y for x, y in zip(sa, sb))}/29 items", flush=True)
    s5.EXT = first_dir
    if pairs:
        exact = sum(a == b for a, b in pairs) / len(pairs)
        within1 = sum(abs(a - b) <= 1 for a, b in pairs) / len(pairs)
        diff = sum(abs(x[2] - x[3]) for x in rows) / len(rows)
        print(f"\nRESULT over {len(rows)} sources x 29 items = {len(pairs)} item scores:")
        print(f"  exact agreement: {exact:.0%}   within one point: {within1:.0%}   Cohen's kappa: {kappa(pairs):.2f}")
        print(f"  average difference in source total: {diff:.1f} points (of 58)")
        print("  Rough guide: kappa above 0.8 = very good, 0.6-0.8 = good, below 0.6 = tighten the rules before the full run.")
        (DATA / "repeatability.json").write_text(json.dumps(dict(sources=rows, exact=exact, within1=within1, kappa=kappa(pairs)), indent=1))
