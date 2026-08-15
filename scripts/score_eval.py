# -*- coding: utf-8 -*-
"""AdmitOR evalproto -- score_eval.py (v2)

Purpose
    Score an OptSkills trajectories.jsonl by comparing each row's numeric
    prediction against its answer. This is the single uniform ruler used for
    every benchmark and every oracle arm in the paper. The scoring rule is
    defined by us and is not shipped with any benchmark, so it is applied
    identically everywhere to keep arms comparable.

    Four tiers are reported:
      strict 1e-6 / standard 1e-4 / loose 1e-2   (relative tolerance)
      round-aware (the headline tier used in the paper's tables): a hit at
        the standard tier, or equality after rounding the prediction to the
        number of decimal places carried by the label.
      Rationale for the round-aware tier: labels are often rounded values
      (for example 10.33), and an exact solution of 10.3333 should not be
      judged wrong.

Inputs
    A trajectories.jsonl produced by an OptSkills eval run. Each line must
    carry sample_id, prediction and answer.

Outputs
    A human-readable report on stdout: record count, unparseable predictions,
    the four tier accuracies, and the list of rows that miss the headline
    tier. Nothing is written to disk.

Note on artifacts: eval trajectories carry the benchmark problem text
verbatim, so they are not redistributed here. Point this script at the
trajectories your own E1 eval run produces (see the README's E1 section).

Example invocation (from the repository root)
    python scripts/score_eval.py \\
        outputs/e1/eval/gate/optmath/trajectories.jsonl --verbose
"""
import argparse
import json
import sys


def to_num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(",", "").rstrip("%")
    try:
        return float(s)
    except ValueError:
        return None


def dec_places(x):
    s = str(x).strip()
    return len(s.split(".")[1]) if "." in s else 0


def rel_match(pred, ans, rel):
    if pred is None or ans is None:
        return False
    return abs(pred - ans) <= max(1e-9, rel * abs(ans))


def round_aware(pred, ans_num, ans_raw):
    if pred is None or ans_num is None:
        return False
    if rel_match(pred, ans_num, 1e-4):
        return True
    try:
        return round(pred, dec_places(ans_raw)) == ans_num
    except Exception:
        return False


def main():
    ap = argparse.ArgumentParser(
        description="Score an OptSkills trajectories.jsonl with the paper's "
        "uniform round-aware ruler."
    )
    ap.add_argument("path", help="path to trajectories.jsonl")
    ap.add_argument(
        "--verbose",
        action="store_true",
        help="also print a summary of the first mismatching " "row's candidate",
    )
    a = ap.parse_args()

    recs = [json.loads(l) for l in open(a.path, encoding="utf-8") if l.strip()]
    n = len(recs)
    print(f"records: {n}")

    parsed = [
        (r, to_num(r.get("prediction")), to_num(r.get("answer")), r.get("answer")) for r in recs
    ]

    unparsed = [r["sample_id"] for r, p, _, _ in parsed if p is None]
    if unparsed:
        print(
            f"prediction unparseable: {len(unparsed)} row(s) "
            f"{unparsed[:5]}{'...' if len(unparsed) > 5 else ''} "
            f"(counted as wrong)"
        )

    for name, rel in [("strict 1e-6", 1e-6), ("standard 1e-4", 1e-4), ("loose 1e-2", 1e-2)]:
        c = sum(1 for _, p, ans, _ in parsed if rel_match(p, ans, rel))
        print(f"  {name}: {c}/{n} = {100.0*c/n:.2f}%")
    ra = sum(1 for _, p, ans, raw in parsed if round_aware(p, ans, raw))
    print(f"  round-aware (headline tier for the tables): " f"{ra}/{n} = {100.0*ra/n:.2f}%")

    miss = [(r, p, ans) for r, p, ans, raw in parsed if not round_aware(p, ans, raw)]
    print(f"\nheadline-tier mismatches: {len(miss)}")
    for r, p, ans in miss:
        line = (
            f"  {r['sample_id']:>12s}  answer={r.get('answer')}  "
            f"prediction={r.get('prediction')}"
        )
        print(line if len(line) < 100 else line[:97] + "...")
    if a.verbose and miss:
        print("\n(--verbose) candidate summary of the first mismatch:")
        print(str(miss[0][0].get("candidate"))[:800])


if __name__ == "__main__":
    sys.exit(main())
