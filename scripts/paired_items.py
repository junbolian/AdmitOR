# -*- coding: utf-8 -*-
"""Per-benchmark paired item counts between judge arms (zero token).

Purpose
    Shows where the downstream differences of Table 2 come from: for each
    benchmark and each pair (AdmitOR, other arm), the number of items that only
    one of the two libraries answers correctly, with the exact two-sided
    McNemar p-value on those discordant items.

Inputs
    --eval-root  directory holding <arm>/<benchmark>/trajectories.jsonl for the
                 four E1 arms (run records, outputs/e1/eval)
    --arm-map    folder name of each arm under eval-root, default
                 gt=gt,vote=vote,runsok=runsok,gate=gate
    --peek       print the directory layout and the keys of the first row, then exit

Scoring
    score_eval.round_aware, imported from this directory, applied to every row;
    unparseable predictions count as wrong, as in Table 2.

Reconciliation gates (stop with exit code 2 on any failure)
    1. every arm has the same item ids per benchmark
    2. per-arm per-benchmark accuracy equals Table 2 to two decimals
    3. the ground-truth arm carries exactly 85 e1_eval_failure rows on OptiBench
       (the R1 basis of Appendix C), searched recursively in each row

Outputs (to --out, default outputs/additional_2026-11)
    paired_items.csv, paired_items.md
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_eval import round_aware, to_num  # noqa: E402

TABLE2 = {  # arm -> benchmark -> accuracy (%), Table 2 of the paper
    "gt":     {"ComplexOR": 66.67, "IndustryOR": 31.00, "Mamo.C": 52.61, "OptMATH": 56.02, "OptiBench": 63.14},
    "runsok": {"ComplexOR": 66.67, "IndustryOR": 35.00, "Mamo.C": 53.08, "OptMATH": 55.42, "OptiBench": 72.40},
    "vote":   {"ComplexOR": 61.11, "IndustryOR": 33.00, "Mamo.C": 53.55, "OptMATH": 54.22, "OptiBench": 72.23},
    "gate":   {"ComplexOR": 66.67, "IndustryOR": 39.00, "Mamo.C": 57.82, "OptMATH": 56.02, "OptiBench": 72.23},
}
EXPECTED_FLAGS = 85  # gt e1_eval_failure rows on OptiBench (R1 basis)
SIZES = {"ComplexOR": 18, "IndustryOR": 100, "Mamo.C": 211, "OptMATH": 166, "OptiBench": 605}


def canon(name):
    n = name.lower().replace("-", "").replace("_", "")
    if "complex" in n and "mamo" not in n:
        return "ComplexOR"
    if "industry" in n:
        return "IndustryOR"
    if "mamo" in n:
        return "Mamo.C"
    if "optibench" in n:
        return "OptiBench"
    if "optmath" in n:
        return "OptMATH"
    return None


def has_flag(x):
    if isinstance(x, dict):
        return any((k == "e1_eval_failure" and bool(v)) or has_flag(v) for k, v in x.items())
    if isinstance(x, list):
        return any(has_flag(v) for v in x)
    return False


def mcnemar_p(b, c):
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2.0 ** n
    return min(1.0, 2.0 * tail)


def load(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        sid = str(r.get("sample_id"))
        ans = r.get("answer")
        out[sid] = (round_aware(to_num(r.get("prediction")), to_num(ans), ans), has_flag(r))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-root", required=True)
    ap.add_argument("--arm-map", default="gt=gt,vote=vote,runsok=runsok,gate=gate")
    ap.add_argument("--out", default="outputs/additional_2026-11")
    ap.add_argument("--peek", action="store_true")
    a = ap.parse_args()
    amap = dict(x.split("=", 1) for x in a.arm_map.split(","))
    arms = ["gt", "vote", "runsok", "gate"]
    if sorted(amap) != sorted(arms):
        print("STOP: --arm-map must name exactly gt, vote, runsok, gate"); sys.exit(2)
    if a.peek:
        print("eval-root folders:", sorted(os.listdir(a.eval_root)))
        for arm in arms:
            d = os.path.join(a.eval_root, amap[arm])
            print(arm, sorted(os.listdir(d)) if os.path.isdir(d) else "MISSING")
        first = os.path.join(a.eval_root, amap[arms[0]])
        b0 = sorted(os.listdir(first))[0]
        row = json.loads(open(os.path.join(first, b0, "trajectories.jsonl"), encoding="utf-8").readline())
        print("first row keys:", sorted(row))
        return

    data = {}
    for arm in arms:
        data[arm] = {}
        for b in sorted(os.listdir(os.path.join(a.eval_root, amap[arm]))):
            c = canon(b)
            p = os.path.join(a.eval_root, amap[arm], b, "trajectories.jsonl")
            if c is None or not os.path.isfile(p):
                continue
            data[arm][c] = load(p)
    stop = []
    for arm in arms:
        for bench, n in SIZES.items():
            rows = data[arm].get(bench)
            if rows is None or len(rows) != n:
                stop.append("%s/%s: %s items, expected %d" % (arm, bench, None if rows is None else len(rows), n))
                continue
            acc = round(100.0 * sum(v[0] for v in rows.values()) / n, 2)
            if abs(acc - TABLE2[arm][bench]) > 0.005:
                stop.append("%s/%s accuracy %.2f, Table 2 %.2f" % (arm, bench, acc, TABLE2[arm][bench]))
            if set(rows) != set(data[arms[0]].get(bench, {})):
                stop.append("%s/%s item ids differ from %s" % (arm, bench, arms[0]))
    flagged = {s for s, v in data.get("gt", {}).get("OptiBench", {}).items() if v[1]}
    if len(flagged) != EXPECTED_FLAGS:
        stop.append("gt OptiBench e1_eval_failure rows: %d, expected %d" % (len(flagged), EXPECTED_FLAGS))
    if stop:
        print("STOP:\n  " + "\n  ".join(stop)); sys.exit(2)

    os.makedirs(a.out, exist_ok=True)
    rows_out = []
    for other in [x for x in arms if x != "gate"]:
        for basis in (["all", "R1"] if other == "gt" else ["all"]):
            tot = [0, 0, 0, 0]
            for bench in SIZES:
                g, o = data["gate"][bench], data[other][bench]
                ids = [s for s in g if not (basis == "R1" and bench == "OptiBench" and s in flagged)]
                both = sum(1 for s in ids if g[s][0] and o[s][0])
                b = sum(1 for s in ids if g[s][0] and not o[s][0])
                c = sum(1 for s in ids if o[s][0] and not g[s][0])
                none = len(ids) - both - b - c
                for i, x in enumerate((both, b, c, none)):
                    tot[i] += x
                rows_out.append(dict(pair="gate vs " + other, basis=basis, benchmark=bench, n=len(ids),
                                     both_right=both, gate_only=b, other_only=c, both_wrong=none,
                                     mcnemar_p=round(mcnemar_p(b, c), 4)))
            rows_out.append(dict(pair="gate vs " + other, basis=basis, benchmark="all items", n=sum(tot),
                                 both_right=tot[0], gate_only=tot[1], other_only=tot[2], both_wrong=tot[3],
                                 mcnemar_p=round(mcnemar_p(tot[1], tot[2]), 4)))
    with open(os.path.join(a.out, "paired_items.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows_out[0])); w.writeheader(); w.writerows(rows_out)
    md = ["| Pair | Basis | Benchmark | n | both right | gate only | other only | both wrong | McNemar p |",
          "|---|---|---|---:|---:|---:|---:|---:|---:|"]
    md += ["| %(pair)s | %(basis)s | %(benchmark)s | %(n)d | %(both_right)d | %(gate_only)d | %(other_only)d | %(both_wrong)d | %(mcnemar_p).4f |" % r
           for r in rows_out]
    open(os.path.join(a.out, "paired_items.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md)); print("\nALL GATES PASS")


if __name__ == "__main__":
    main()
