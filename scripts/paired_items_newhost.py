# -*- coding: utf-8 -*-
"""Per-benchmark paired item counts between libraries evaluated on a new host (zero token).

Purpose
    The counterpart of paired_items.py for the downstream run on a new host model
    (deepseek-v4-flash), where three libraries built from the stored E1 trajectories
    (gate_asdeployed, panel_base_3of3, vote) were evaluated on the 1,100 items. For each
    benchmark and each pair (target, other) it counts the items that only one of the two
    libraries answers correctly and gives the exact two-sided McNemar p-value. It also
    writes the per-arm per-benchmark accuracy with the macro and item-weighted averages,
    and the number of e1_eval_failure rows per arm.

    paired_items.py itself cannot run on these arms: its gates require the four E1 arms
    and the Table 2 accuracies. This wrapper imports load, canon, mcnemar_p and SIZES from
    paired_items.py unchanged and replaces the Table 2 gate with an internal one.

Inputs
    --eval-root  directory holding <arm>/<benchmark>/trajectories.jsonl
    --arms       comma-separated arm folder names, default
                 gate_asdeployed,panel_base_3of3,vote
    --target     the arm every other arm is compared with, default gate_asdeployed
    --out        output directory

Scoring
    score_eval.round_aware through paired_items.load; unparseable predictions count as wrong.

Gates (stop with exit code 2 on any failure)
    1. every arm and benchmark: the wrapper's accuracy equals the round-aware accuracy that
       score_eval.py prints for the same trajectories.jsonl, to two decimals
    2. identical item ids across the arms per benchmark
    3. benchmark sizes 18 / 100 / 211 / 166 / 605

Outputs (to --out)
    paired_items_newhost.csv, paired_items_newhost.md, accuracy_newhost.csv, accuracy_newhost.md

Reproduce (from the repository root)
    python scripts/paired_items_newhost.py --eval-root <run>/eval_serial --out <run>/analysis
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from paired_items import SIZES, canon, load, mcnemar_p  # noqa: E402

ORDER = ["ComplexOR", "IndustryOR", "Mamo.C", "OptMATH", "OptiBench"]


def score_eval_accuracy(path):
    out = subprocess.run([sys.executable, os.path.join(HERE, "score_eval.py"), path],
                         capture_output=True, text=True, check=True).stdout
    m = re.search(r"round-aware[^:]*:\s*(\d+)/(\d+)\s*=\s*([\d.]+)%", out)
    if not m:
        raise RuntimeError("score_eval.py output without a round-aware line for %s" % path)
    return float(m.group(3)), int(m.group(2))


def main():
    ap = argparse.ArgumentParser(description="Paired item counts for libraries evaluated on a new host.")
    ap.add_argument("--eval-root", required=True)
    ap.add_argument("--arms", default="gate_asdeployed,panel_base_3of3,vote")
    ap.add_argument("--target", default="gate_asdeployed")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    arms = a.arms.split(",")
    if a.target not in arms:
        print("STOP: --target must be one of --arms"); sys.exit(2)

    data, paths = {}, {}
    for arm in arms:
        data[arm] = {}
        d = os.path.join(a.eval_root, arm)
        for b in sorted(os.listdir(d)):
            c = canon(b)
            p = os.path.join(d, b, "trajectories.jsonl")
            if c is None or not os.path.isfile(p):
                continue
            data[arm][c] = load(p)
            paths[(arm, c)] = p

    stop, acc = [], {}
    for arm in arms:
        for bench, n in SIZES.items():
            rows = data[arm].get(bench)
            if rows is None or len(rows) != n:
                stop.append("%s/%s: %s items, expected %d" % (arm, bench, None if rows is None else len(rows), n))
                continue
            mine = round(100.0 * sum(v[0] for v in rows.values()) / n, 2)
            ref, ref_n = score_eval_accuracy(paths[(arm, bench)])
            if ref_n != n or abs(mine - ref) > 0.005:
                stop.append("%s/%s accuracy %.2f, score_eval.py %.2f (%d records)" % (arm, bench, mine, ref, ref_n))
            if set(rows) != set(data[arms[0]].get(bench, {})):
                stop.append("%s/%s item ids differ from %s" % (arm, bench, arms[0]))
            acc[(arm, bench)] = mine
    if stop:
        print("STOP:\n  " + "\n  ".join(stop)); sys.exit(2)

    os.makedirs(a.out, exist_ok=True)
    acc_rows = []
    for arm in arms:
        right = sum(sum(v[0] for v in data[arm][b].values()) for b in ORDER)
        flagged = sum(sum(v[1] for v in data[arm][b].values()) for b in ORDER)
        row = {"arm": arm}
        row.update({b: "%.2f" % acc[(arm, b)] for b in ORDER})
        row["macro"] = "%.2f" % (sum(acc[(arm, b)] for b in ORDER) / len(ORDER))
        row["item_weighted"] = "%.2f" % (100.0 * right / sum(SIZES.values()))
        row["e1_eval_failure_rows"] = flagged
        acc_rows.append(row)
    with open(os.path.join(a.out, "accuracy_newhost.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(acc_rows[0])); w.writeheader(); w.writerows(acc_rows)
    md = ["| Library | " + " | ".join(ORDER) + " | Macro | Item-weighted | e1_eval_failure rows |",
          "|---|" + "---:|" * (len(ORDER) + 3)]
    md += ["| `%s` | %s | %s | %s | %d |" % (r["arm"], " | ".join(r[b] for b in ORDER), r["macro"],
                                            r["item_weighted"], r["e1_eval_failure_rows"]) for r in acc_rows]
    open(os.path.join(a.out, "accuracy_newhost.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
    print("\n".join(md) + "\n")

    out = []
    for other in [x for x in arms if x != a.target]:
        tot = [0, 0, 0, 0]
        for bench in ORDER:
            g, o = data[a.target][bench], data[other][bench]
            both = sum(1 for s in g if g[s][0] and o[s][0])
            b = sum(1 for s in g if g[s][0] and not o[s][0])
            c = sum(1 for s in g if o[s][0] and not g[s][0])
            none = len(g) - both - b - c
            for i, x in enumerate((both, b, c, none)):
                tot[i] += x
            out.append(dict(pair="%s vs %s" % (a.target, other), benchmark=bench, n=len(g), both_right=both,
                            target_only=b, other_only=c, both_wrong=none, mcnemar_p=round(mcnemar_p(b, c), 4)))
        out.append(dict(pair="%s vs %s" % (a.target, other), benchmark="all items", n=sum(tot), both_right=tot[0],
                        target_only=tot[1], other_only=tot[2], both_wrong=tot[3],
                        mcnemar_p=round(mcnemar_p(tot[1], tot[2]), 4)))
    with open(os.path.join(a.out, "paired_items_newhost.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0])); w.writeheader(); w.writerows(out)
    md = ["| Pair | Benchmark | n | both right | target only | other only | both wrong | McNemar p |",
          "|---|---|---:|---:|---:|---:|---:|---:|"]
    md += ["| %(pair)s | %(benchmark)s | %(n)d | %(both_right)d | %(target_only)d | %(other_only)d | %(both_wrong)d | %(mcnemar_p).4f |" % r
           for r in out]
    open(os.path.join(a.out, "paired_items_newhost.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
    print("\n".join(md)); print("\nALL GATES PASS")


if __name__ == "__main__":
    main()
