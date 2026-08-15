"""AdmitOR evalproto -- paired_bootstrap.py (v1)

Paired stratified bootstrap for arm-vs-arm macro deltas on the E1 eval
campaign, using the SAME round-aware ruler as score_eval.py (functions
copied verbatim). Items are paired per (benchmark, sample_id); resampling
is within-benchmark (stratified), preserving plate sizes; macro = mean of
per-plate accuracies. Reports point deltas and percentile 95% CIs.

Inputs
    --eval-root  directory holding <arm>/<benchmark>/trajectories.jsonl for
                 every arm named in --pairs
    --pairs      one or more "x:y" arm pairs to compare (default
                 gate:vote gate:gt)
    --reps       bootstrap resamples (default 10000)
    --seed       RNG seed (default 42)

Outputs
    One line per pair on stdout: the point macro delta in percentage points,
    the percentile 95 percent confidence interval, and P(delta > 0). Nothing
    is written to disk.

Note on artifacts: eval trajectories carry the benchmark problem text
verbatim, so they are not redistributed here. Point --eval-root at the
trajectories your own E1 eval run produces (see the README's E1 section).

Example invocation (from the repository root)
    python scripts/paired_bootstrap.py --eval-root outputs/e1/eval \\
        --pairs gate:vote gate:gt --reps 10000 --seed 42
"""

from __future__ import annotations

import argparse
import json
import os
import random
from typing import Dict, List


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


PLATES = ["complexor", "industryor", "mamo_c", "optmath", "optibench"]


def load_arm(root: str, arm: str) -> Dict[str, Dict[str, int]]:
    out: Dict[str, Dict[str, int]] = {}
    for plate in PLATES:
        path = os.path.join(root, arm, plate, "trajectories.jsonl")
        plate_map: Dict[str, int] = {}
        with open(path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                p = to_num(r.get("prediction"))
                ans = to_num(r.get("answer"))
                plate_map[str(r.get("sample_id"))] = int(round_aware(p, ans, r.get("answer")))
        out[plate] = plate_map
    return out


def macro(binvecs: Dict[str, List[int]]) -> float:
    return sum(100.0 * sum(v) / len(v) for v in binvecs.values()) / len(binvecs)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-root", required=True)
    ap.add_argument("--pairs", nargs="+", default=["gate:vote", "gate:gt"])
    ap.add_argument("--reps", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=42)
    a = ap.parse_args()

    arms_needed = sorted({x for p in a.pairs for x in p.split(":")})
    data = {arm: load_arm(a.eval_root, arm) for arm in arms_needed}

    for pair in a.pairs:
        x, y = pair.split(":")
        keys = {plate: sorted(set(data[x][plate]) & set(data[y][plate])) for plate in PLATES}
        vx = {plate: [data[x][plate][k] for k in keys[plate]] for plate in PLATES}
        vy = {plate: [data[y][plate][k] for k in keys[plate]] for plate in PLATES}
        point = macro(vx) - macro(vy)
        rng = random.Random(a.seed)
        deltas = []
        for _ in range(a.reps):
            bx, by = {}, {}
            for plate in PLATES:
                n = len(keys[plate])
                idx = [rng.randrange(n) for _ in range(n)]
                bx[plate] = [vx[plate][i] for i in idx]
                by[plate] = [vy[plate][i] for i in idx]
            deltas.append(macro(bx) - macro(by))
        deltas.sort()
        lo = deltas[int(0.025 * a.reps)]
        hi = deltas[int(0.975 * a.reps) - 1]
        frac_pos = sum(1 for d in deltas if d > 0) / a.reps
        print(
            f"{x} - {y}: macro delta {point:+.2f}pp, "
            f"95% CI [{lo:+.2f}, {hi:+.2f}], P(delta>0) = {frac_pos:.4f}"
        )


if __name__ == "__main__":
    main()
