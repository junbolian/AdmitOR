# -*- coding: utf-8 -*-
"""AdmitOR E0 -- e0_scorecard.py

Purpose
    The E0 host-calibration gate. Compare the accuracy numbers reported in
    the OptSkills paper against the numbers obtained by re-running the host
    locally, and pass or fail each benchmark on a plus or minus 3 percentage
    point tolerance. E0 exists to establish that the experimental bench
    reproduces the host before any AdmitOR result is measured on it.

Inputs
    A scorecard JSON (default scorecard.json in the working directory). If
    the file does not exist, a blank template is written and the script
    exits so the operator can fill it in. Template shape, where the paper
    column is transcribed from OptSkills Table 1 and the ours column holds
    the locally reproduced numbers:
    {
      "tolerance_pp": 3.0,
      "rows": {
        "OptiBench":     {"paper": null, "ours": null},
        "Mamo.C":        {"paper": null, "ours": null},
        "OptMATH-Bench": {"paper": null, "ours": null},
        "IndustryOR":    {"paper": null, "ours": null},
        "ComplexOR":     {"paper": null, "ours": null}
      },
      "meta": {"run_date": "", "model_string": "", "api_note": ""}
    }

Outputs
    A per-benchmark table on stdout with the delta in percentage points and a
    PASS or FAIL per row, followed by the overall E0 verdict. Nothing is
    written to disk unless the template had to be created.

Filling the ours column from the released E0 run records
    --eval-root DIR  directory holding <plate>/trajectories.jsonl for every
                     row that carries a "plate" key; ours is then the
                     round-aware accuracy computed with score_eval.py's
                     ruler, and a macro row is printed when every row is
                     filled. release/e0/scorecard.json (in git) carries the
                     reported column quoted from the host paper and the plate
                     of each row; the E0 trajectories are the release asset
                     admitor-v1.1.0-run-records-e0.zip.

Example invocation (from the repository root)
    python scripts/e0_scorecard.py release/e0/scorecard.json --eval-root <run-records>/outputs/eval

Paper location
    Appendix C Table 9 (Reported, Ours, delta per benchmark and the macro row).
"""
import json
import os
import sys

_args = sys.argv[1:]
if "-h" in _args or "--help" in _args:
    print(__doc__)
    sys.exit(0)
EVAL_ROOT = None
if "--eval-root" in _args:
    _i = _args.index("--eval-root")
    EVAL_ROOT = _args[_i + 1]
    del _args[_i:_i + 2]
PATH = _args[0] if _args else "scorecard.json"


def ours_from_eval(root, plate):
    """Round-aware accuracy (%) of <root>/<plate>/trajectories.jsonl, scored with
    score_eval.round_aware exactly as score_eval.py's main() does."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from score_eval import round_aware, to_num

    recs = [json.loads(l) for l in open(os.path.join(root, plate, "trajectories.jsonl"),
                                        encoding="utf-8") if l.strip()]
    ok = sum(1 for r in recs if round_aware(to_num(r.get("prediction")), to_num(r.get("answer")),
                                            r.get("answer")))
    return round(100.0 * ok / len(recs), 2), len(recs)

TEMPLATE = {
    "tolerance_pp": 3.0,
    "rows": {
        k: {"paper": None, "ours": None}
        for k in ["OptiBench", "Mamo.C", "OptMATH-Bench", "IndustryOR", "ComplexOR"]
    },
    "meta": {"run_date": "", "model_string": "", "api_note": ""},
}

if not os.path.exists(PATH):
    json.dump(TEMPLATE, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(
        f"template written to {PATH}: fill in the paper column (Table 1) "
        f"and the ours column, then run this script again."
    )
    sys.exit(0)

cfg = json.load(open(PATH, encoding="utf-8"))
tol = cfg.get("tolerance_pp", 3.0)
rows = cfg["rows"]
if EVAL_ROOT:
    for name, r in rows.items():
        if r.get("plate"):
            r["ours"], r["n"] = ours_from_eval(EVAL_ROOT, r["plate"])

print(f"{'benchmark':14s} {'paper':>7s} {'ours':>7s} {'d(pp)':>7s}  verdict")
print("-" * 50)
all_pass, filled = True, 0
for name, r in rows.items():
    p, o = r.get("paper"), r.get("ours")
    if p is None or o is None:
        print(f"{name:14s} {'--':>7s} {'--':>7s} {'--':>7s}  (not filled in)")
        continue
    filled += 1
    d = o - p
    ok = abs(d) <= tol
    all_pass &= ok
    print(f"{name:14s} {p:7.2f} {o:7.2f} {d:+7.2f}  " f"{'PASS' if ok else 'FAIL'}")
print("-" * 50)
if filled and filled == len(rows):
    mp = sum(r["paper"] for r in rows.values()) / filled
    mo = sum(r["ours"] for r in rows.values()) / filled
    print(f"{'Macro':14s} {mp:7.2f} {mo:7.2f} {mo - mp:+7.2f}")
    print("-" * 50)
if filled == 0:
    print("no numbers filled in yet.")
elif filled < len(rows):
    print(
        f"{filled}/{len(rows)} rows filled in; complete the table before "
        f"reading the E0 verdict."
    )
else:
    print(
        "E0 verdict: "
        + (
            "PASS -- the experimental bench is calibrated against the host."
            if all_pass
            else "FAIL -- investigate or roll the host back per the contingency plan "
            "in the README."
        )
    )
print(f"meta: {cfg.get('meta')}")
