# -*- coding: utf-8 -*-
"""Merge the problem-level and candidate-level rows of the judge suite (zero token).

Inputs
    --problem    outputs/additional_2026-11/problem_level.csv   (judge_suite.py)
    --candidate  outputs/additional_2026-11/candidate/03_decomposition_candidate.csv
                 (candidate_crosstab.py; the re-derived deployed gate is named
                 gate_asdeployed_rederived so that it is not confused with the
                 stored arm gate_asdeployed)
    --out        outputs/additional_2026-11/judge_suite_table.md

Reconciliation gate (exit code 2 on failure): the re-derived Table 3 rows must
equal the published candidate-level counts.
"""
import argparse
import csv
import sys

GATES = {"panel_base_2of3": (610, 45), "panel_base_3of3": (516, 32),
         "gate_asdeployed_rederived": (413, 30), "gate_tau": (344, 22)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--problem", default="outputs/additional_2026-11/problem_level.csv")
    ap.add_argument("--candidate", default="outputs/additional_2026-11/candidate/03_decomposition_candidate.csv")
    ap.add_argument("--out", default="outputs/additional_2026-11/judge_suite_table.md")
    a = ap.parse_args()
    prob = {r["judge"]: r for r in csv.DictReader(open(a.problem, encoding="utf-8"))}
    cand = {r["judge"]: r for r in csv.DictReader(open(a.candidate, encoding="utf-8"))}
    fails = []
    for j, (adm, poi) in GATES.items():
        r = cand.get(j)
        if r is None or (int(r["admitted"]), int(r["poison"])) != (adm, poi):
            fails.append((j, None if r is None else (r["admitted"], r["poison"]), (adm, poi)))
    if fails:
        print("STOP: Table 3 reconciliation failed:", fails); sys.exit(2)
    L = ["| Judge | Model calls | Solver runs | Certified problems | Wrong certificates | False % | "
         "Admitted trajectories | Wrong admissions | Precision | Recall |",
         "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for name in ("runsok", "vote"):
        if name in cand:
            c = cand[name]
            L.append("| `%s` | - | - | - | - | - | %s | %s | %s | %s |" % (name, c["admitted"], c["poison"], c["precision"], c["recall"]))
    for j, p in prob.items():
        c = cand.get("gate_asdeployed_rederived" if j == "gate_asdeployed" else j, {})
        L.append("| `%s` | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            j, p["model_calls"], p["solver_runs"], p["certified"], p["wrong"], p["false_pct"],
            c.get("admitted", "n/a"), c.get("poison", "n/a"), c.get("precision", "n/a"), c.get("recall", "n/a")))
    open(a.out, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("\n".join(L)); print("\nRECONCILIATION PASSED")


if __name__ == "__main__":
    main()
