# -*- coding: utf-8 -*-
"""Judge ablation: candidate-level admission precision and recall (zero token).

Purpose
    The unit of Section 4.2 is the candidate, not the problem. This computes
    admitted / poison / precision / recall for every judge on the same
    footing, against the vault, with the host equality rule, ex dev split.

Definitions, from the released code
    admitted  a host trajectory labelled positive under the judge's
              certificate (label_oracle.host_label)
    poison    an admitted trajectory whose own result does not match the
              vault answer under the same rule
    recall    admitted-and-correct divided by all vault-correct trajectories
              in the non-dev stream (637; the denominator that makes runsok
              1.000)

Reconciliation gate, checked before any new row is reported
    runsok 878 / 241 / 0.726 / 1.000, vote 721 / 93 / 0.871 / 0.986,
    gate_asdeployed 413 / 30 / 0.927 / 0.601

Inputs
    --arms   name=path pairs, repeatable: relabeled arm files
             <host>/outputs/e1/arms/{runsok,vote,gate}.jsonl (private, not
             distributed) and the derived judges written by
             panel_base_judges.py as relabeled rows
    --vault  datasets/vault/optmath-train-300-labels.jsonl (in git)
    --out    default reanalysis/reviewer_round

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

Reproduce (from the repository root)
    python scripts/candidate_crosstab.py --arms runsok=<host>/outputs/e1/arms/runsok.jsonl --arms vote=<host>/outputs/e1/arms/vote.jsonl --arms gate_asdeployed=<host>/outputs/e1/arms/gate.jsonl

Outputs
    <out>/03_decomposition_candidate.csv and a markdown block on stdout

Paper location
    Section 4.2 Table 3 and Appendix C "Judge ablation details".
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)  # scripts/, for label_oracle
from label_oracle import host_label, row_candidates  # noqa: E402

DEV = {"sample_%d" % i for i in (1, 2, 3, 4, 5)}
GATE = {"runsok": (878, 241, 0.726, 1.000),
        "vote": (721, 93, 0.871, 0.986),
        "gate_asdeployed": (413, 30, 0.927, 0.601)}


def main():
    ap = argparse.ArgumentParser(description="Task 3.3 candidate crosstab.")
    ap.add_argument("--vault", default="datasets/vault/optmath-train-300-labels.jsonl")
    ap.add_argument("--arms", action="append", required=True,
                    help="name=path, repeatable")
    ap.add_argument("--out", default="reanalysis/reviewer_round")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    vault = {}
    for line in open(a.vault, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            vault["sample_%s" % r["idx"]] = str(r.get("answer"))

    # denominator for recall: all vault-correct trajectories, non-dev
    correct_total = None
    rows, fails = [], []
    for spec in a.arms:
        name, path = spec.split("=", 1)
        adm = poison = elig = 0
        adm_correct = 0
        ctot = 0
        for line in open(path, encoding="utf-8"):
            if not line.strip():
                continue
            row = json.loads(line)
            sid = str(row.get("sample_id"))
            if sid in DEV:
                continue
            ans = vault.get(sid)
            cands = row_candidates(row)
            for c in cands:
                if ans is not None and host_label(c, ans) == "positive":
                    ctot += 1
            if not row.get("eligible"):
                continue
            elig += 1
            gt = str(row.get("answer", ""))
            for c in cands:
                if host_label(c, gt) != "positive":
                    continue
                adm += 1
                if ans is not None and host_label(c, ans) == "positive":
                    adm_correct += 1
                else:
                    poison += 1
        if correct_total is None:
            correct_total = ctot
        prec = (adm - poison) / adm if adm else float("nan")
        rec = adm_correct / correct_total if correct_total else float("nan")
        rows.append(dict(judge=name, admitted=adm, poison=poison,
                         precision=round(prec, 4), recall=round(rec, 4),
                         eligible_problems=elig,
                         vault_correct_total=correct_total))
        if name in GATE:
            ea, ep, epr, ere = GATE[name]
            ok = (adm == ea and poison == ep
                  and abs(prec - epr) < 0.0015 and abs(rec - ere) < 0.0015)
            if not ok:
                fails.append((name, adm, poison, round(prec, 4), round(rec, 4),
                              GATE[name]))

    print("| Judge | admitted | poison | precision | recall | eligible problems |")
    print("|---|---:|---:|---:|---:|---:|")
    for r in rows:
        print("| `%s` | %d | %d | %.3f | %.3f | %d |"
              % (r["judge"], r["admitted"], r["poison"], r["precision"],
                 r["recall"], r["eligible_problems"]))
    print()
    print("recall denominator (vault-correct trajectories, non-dev): %d" % correct_total)
    print()
    if fails:
        print("RECONCILIATION FAILED:")
        for f in fails:
            print("   ", f)
        return 1
    print("RECONCILIATION PASSED for every gated row.")
    with open(os.path.join(a.out, "03_decomposition_candidate.csv"), "w",
              encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print("wrote", os.path.join(a.out, "03_decomposition_candidate.csv"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
