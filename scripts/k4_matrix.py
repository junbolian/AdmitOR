"""AdmitOR K4 -- k4_matrix.py

Mines the existing certification artifacts (zero new model calls) into the
preregistered K4 family x error-type matrix: for every candidate in every
certification run, classify its terminal outcome and aggregate by
candidate arm (family/strategy). K4 asks whether the matrix is near
uniform (which would weaken the consensus and profiling arguments) or
structured (which supports them).

Inputs
    --e1-runs   directory of per-sample certification runs, each holding a
                verdict_full.json (for example artifacts/e1/certify_runs)
    --out       optional path for the matrix as JSON
    --peek      print the JSON keys of one verdict_full.json and one
                candidate record so the field mapping can be corrected if
                the schema differs

Outputs
    The arm-by-outcome matrix and the pairwise total-variation distances
    between arm outcome profiles, printed to stdout; with --out, the same
    matrix as {"runs": <n>, "matrix": {...}} JSON.

    Note: this script emits the contingency table only. The chi-squared test
    of independence reported in the paper is computed from that table; see
    the E3 subsection of the README for the exact one-line command that
    reproduces the reported statistic from the shipped k4_matrix.json.

Example invocation (from the repository root)
    python scripts/k4_matrix.py --e1-runs artifacts/e1/certify_runs \\
        --out artifacts/e3/k4_matrix.json
"""

from __future__ import annotations

import argparse
import json
import os
from collections import Counter, defaultdict


def load_verdicts(root):
    for sid in sorted(os.listdir(root)):
        vf = os.path.join(root, sid, "verdict_full.json")
        if os.path.isfile(vf):
            try:
                yield sid, json.load(open(vf, encoding="utf-8"))
            except Exception:
                continue


def candidate_records(v):
    """Yield (cand_id, record) across known schema layouts.

    admitor-core rich verdicts store per-candidate data in parallel
    top-level dicts keyed by candidate id: statuses, objectives,
    families. Nested candidate containers are supported as fallback.
    """
    sts = v.get("statuses")
    if isinstance(sts, dict) and sts:
        objs = v.get("objectives") if isinstance(v.get("objectives"), dict) else {}
        fams = v.get("families") if isinstance(v.get("families"), dict) else {}
        for cid in sorted(sts):
            yield cid, {"statuses": sts[cid], "objectives": objs.get(cid), "family": fams.get(cid)}
        return
    for key in ("candidates", "per_candidate", "panel"):
        obj = v.get(key)
        if isinstance(obj, dict):
            for cid, rec in obj.items():
                yield cid, rec if isinstance(rec, dict) else {"value": rec}
            return
        if isinstance(obj, list):
            for rec in obj:
                if isinstance(rec, dict):
                    cid = rec.get("id") or rec.get("candidate") or rec.get("name")
                    if cid:
                        yield cid, rec
            return


def statuses_of(rec):
    for key in ("statuses", "instance_statuses", "status_by_instance"):
        s = rec.get(key)
        if isinstance(s, list):
            out = []
            for x in s:
                if isinstance(x, dict):
                    out.append(str(x.get("status", x)))
                else:
                    out.append(str(x))
            return out
        if isinstance(s, dict):
            return [str(s[k]) for k in sorted(s)]
    s = rec.get("status")
    return [str(s)] if s is not None else []


def classify(rec, in_clique):
    """Candidate-level terminal outcome."""
    sts = [s.lower() for s in statuses_of(rec)]
    if in_clique:
        return "clique member"
    if not sts:
        return "no status recorded"
    if all(("crash" in s or "error" in s or "failed" in s) for s in sts):
        return "all runs crashed or failed"
    if any("crash" in s or "error" in s for s in sts):
        return "partial crashes"
    if any("infeasible" in s or "unbounded" in s for s in sts):
        return "infeasible on instances"
    return "solved, value excluded from clique"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--e1-runs", required=True)
    ap.add_argument("--out", default=None)
    ap.add_argument("--peek", action="store_true")
    a = ap.parse_args()

    if a.peek:
        for sid, v in load_verdicts(a.e1_runs):
            print(f"[peek] {sid} top-level keys: {sorted(v.keys())}")
            for cid, rec in candidate_records(v):
                print(f"[peek] first candidate id: {cid}")
                print(f"[peek] statuses: {statuses_of(rec)}")
                break
            else:
                print("[peek] statuses raw:", type(v.get("statuses")), str(v.get("statuses"))[:200])
            return
        print("[peek] no verdict_full.json found under", a.e1_runs)
        return

    matrix = defaultdict(Counter)
    n_runs = 0
    for sid, v in load_verdicts(a.e1_runs):
        n_runs += 1
        clique = set(v.get("clique") or [])
        for cid, rec in candidate_records(v):
            arm = str(cid)
            matrix[arm][classify(rec, cid in clique)] += 1

    if not matrix:
        print("[k4] no candidates parsed; run --peek and report the schema")
        return

    outcomes = sorted({o for c in matrix.values() for o in c})
    arms = sorted(matrix)
    widest = max(len(x) for x in arms)
    header = " " * widest + "  " + "  ".join(f"{o[:26]:>26}" for o in outcomes)
    print(f"[k4] {n_runs} certification runs")
    print(header)
    rows = {}
    for arm in arms:
        total = sum(matrix[arm].values())
        rows[arm] = {o: matrix[arm][o] for o in outcomes}
        cells = "  ".join(f"{matrix[arm][o]:>26}" for o in outcomes)
        print(f"{arm:<{widest}}  {cells}   (n={total})")

    # simple structure statistic: total variation distance between each
    # pair of arm outcome profiles (0 = identical profiles = K4 trouble)
    def profile(arm):
        t = sum(matrix[arm].values())
        return {o: matrix[arm][o] / t for o in outcomes}

    print("\n[k4] pairwise total-variation distance between arm profiles")
    for i, x in enumerate(arms):
        for y in arms[i + 1 :]:
            px, py = profile(x), profile(y)
            tv = 0.5 * sum(abs(px[o] - py[o]) for o in outcomes)
            print(f"  {x} vs {y}: {tv:.3f}")
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        json.dump({"runs": n_runs, "matrix": rows}, open(a.out, "w"), indent=1)
        print(f"\n[k4] written -> {a.out}")


if __name__ == "__main__":
    main()
