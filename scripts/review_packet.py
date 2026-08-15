"""AdmitOR E3 forensics -- review_packet.py

Assembles one human-review markdown packet per disputed admission:
problem text, certified value vs vault label, gap, and the clique
members' code, so a reviewer can classify each case as
(a) gate model defect, (b) label error, or (c) ambiguous problem text
with a legitimate alternative reading.

Inputs
    --report     the E3 replay report JSON, whose wrong_admission_detail
                 list drives one packet per disputed admission
    --e1-runs    directory of per-sample certification runs, each holding a
                 verdict_full.json and the clique members' generated code
    --workorder  the E1 gate work order jsonl, used to recover problem text
    --out        output directory for the markdown packets

Outputs
    <out>/<sample_id>.md, one markdown packet per disputed admission, each
    with an unfilled classification checklist for the reviewer.

Example invocation (from the repository root)
    python scripts/review_packet.py \\
        --report artifacts/e3/e3_report_v06.json \\
        --e1-runs artifacts/e1/certify_runs \\
        --workorder outputs/e1/gate_workorder.jsonl \\
        --out outputs/e3/review
"""

from __future__ import annotations

import argparse
import glob
import json
import os


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", required=True)
    ap.add_argument("--e1-runs", required=True)
    ap.add_argument("--workorder", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = json.load(open(a.report, encoding="utf-8"))
    sid_to_q = {}
    for l in open(a.workorder, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            sid_to_q[str(r.get("sample_id"))] = r.get("question", "")
    os.makedirs(a.out, exist_ok=True)
    n = 0
    for w in rep.get("wrong_admission_detail", []):
        sid = w["sample_id"]
        run_dir = os.path.join(a.e1_runs, sid)
        vf = os.path.join(run_dir, "verdict_full.json")
        v = json.load(open(vf, encoding="utf-8")) if os.path.isfile(vf) else {}
        clique = v.get("clique") or []
        lines = [
            f"# {sid}",
            "",
            f"certified: {w['certified']}",
            f"vault label: {w['vault_answer']}",
            f"relative gap: {w.get('rel_gap')}",
            f"clique: {clique}  informative: {w.get('informative')}",
            "",
            "## Classification (fill in)",
            "[ ] (a) gate model defect: text states a constraint the",
            "        clique's model drops or misreads",
            "[ ] (b) label error: text has one reasonable reading and the",
            "        clique's value is correct under it",
            "[ ] (c) ambiguity: text supports multiple readings; clique's",
            "        reading is legitimate but differs from the labeler's",
            "notes:",
            "",
            "## Problem text",
            "",
            sid_to_q.get(sid, "(question not found in workorder)"),
            "",
        ]
        for cid in clique:
            for path in glob.glob(os.path.join(run_dir, "runs", "*", f"{cid}.py")) + glob.glob(
                os.path.join(run_dir, f"{cid}.py")
            ):
                code = open(path, encoding="utf-8").read()
                lines += [f"## Clique member {cid}", "", "```python", code, "```", ""]
                break
        with open(os.path.join(a.out, f"{sid}.md"), "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        n += 1
    print(f"[review] wrote {n} packets -> {a.out}")


if __name__ == "__main__":
    main()
