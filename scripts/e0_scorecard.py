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

Example invocation (from the repository root)
    python scripts/e0_scorecard.py artifacts/e0/scorecard.json
"""
import json
import os
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else "scorecard.json"

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
