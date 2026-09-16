"""Assemble release/reviewer_round/03_decomposition.md from script outputs (zero token).

Purpose
    03_decomposition.md was assembled in two parts: panel_base_judges.py writes
    sections 3.2 and 3.4, task3_additions.py appends additions (a) to (c), and
    section 3.3 (candidate-level precision and recall) was originally pasted
    in by hand from candidate_crosstab.py's stdout. This script builds section
    3.3 from candidate_crosstab.py's CSV instead, so every number in the file
    is script output. Precision and recall are recomputed from the integer
    counts in the CSV (admitted, poison, vault-correct total).

    One sentence is a recorded fact about the original run, not recomputable
    from the released records: re-running the vote relabel reproduced the
    private arm file byte-identically (128,677,611 bytes). The released arm
    files are scrubbed copies, so their sizes differ; the sentence is kept as
    provenance and is not a manuscript number.

Inputs
    --problem-md     <out>/03_decomposition.md as written by panel_base_judges.py
                     and extended by task3_additions.py (produced from git + run records)
    --candidate-csv  <out>/03_decomposition_candidate.csv from candidate_crosstab.py
                     (git + run records)
    --out            default: overwrite --problem-md in place

Reproduce (from the repository root, after panel_base_judges.py,
task3_additions.py and candidate_crosstab.py have written into reanalysis/reviewer_round)
    python scripts/assemble_decomposition_report.py --problem-md reanalysis/reviewer_round/03_decomposition.md --candidate-csv reanalysis/reviewer_round/03_decomposition_candidate.csv --out release/reviewer_round/03_decomposition.md

Outputs
    <out>, the full markdown report.

Paper location
    Section 4.2 Table 3 and Appendix C "Judge ablation details".
"""
import argparse
import csv
import sys

GATE = {"runsok": (878, 241, 0.726, 1.000),
        "vote": (721, 93, 0.871, 0.986),
        "gate_asdeployed": (413, 30, 0.927, 0.601)}
ORDER = ["runsok", "vote", "gate_asdeployed", "panel_base_2of3", "panel_base_3of3", "gate_tau"]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--problem-md", required=True)
    ap.add_argument("--candidate-csv", required=True)
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    rows = {r["judge"]: r for r in csv.DictReader(open(a.candidate_csv, encoding="utf-8", newline=""))}
    missing = [j for j in ORDER if j not in rows]
    if missing:
        sys.exit("candidate CSV lacks judges: %s" % missing)
    stats = {}
    for j in ORDER:
        r = rows[j]
        adm, poi, tot = int(r["admitted"]), int(r["poison"]), int(r["vault_correct_total"])
        stats[j] = (adm, poi, (adm - poi) / adm, (adm - poi) / tot, int(r["eligible_problems"]), tot)
    for j, (ea, ep, epr, ere) in GATE.items():
        adm, poi, pr, re_, _, _ = stats[j]
        if (adm, poi, round(pr, 3), round(re_, 3)) != (ea, ep, epr, ere):
            sys.exit("reconciliation gate failed for %s: %s" % (j, stats[j][:4]))
    totals = {s[5] for s in stats.values()}
    if len(totals) != 1:
        sys.exit("inconsistent recall denominators: %s" % totals)

    gate_txt = ", ".join("%s %d / %d / %.3f / %.3f" % ((j,) + stats[j][:4]) for j in GATE)
    L = [
        "## 3.3 Candidate-level admission precision (host equality rule, against the vault, ex dev)",
        "",
        "Reconciliation gate passed before these rows were accepted: %s." % gate_txt,
        "",
        "`label_oracle.py` was not modified. The derived verdicts are already in GateOracle shape, "
        "so the existing gate mode was pointed at each judge's verdict directory. Rule 9 proof: "
        "re-running the vote arm reproduced the stored file byte-identically (128,677,611 bytes).",
        "",
        "| Judge | admitted | poison | precision | recall | eligible problems |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for j in ORDER:
        adm, poi, pr, re_, elig, _ = stats[j]
        L.append("| `%s` | %d | %d | %.3f | %.3f | %d |" % (j, adm, poi, pr, re_, elig))
    L += ["", "Recall denominator (vault-correct trajectories, non-dev): %d." % totals.pop(), ""]

    base = open(a.problem_md, encoding="utf-8", newline="").read()
    if "## 3.3 Candidate-level" in base:
        sys.exit("--problem-md already contains section 3.3; pass the unassembled file")
    text = base.rstrip("\n") + "\n\n\n" + "\n".join(L) + "\n"
    out = a.out or a.problem_md
    open(out, "w", encoding="utf-8", newline="\n").write(text)
    print("wrote", out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
