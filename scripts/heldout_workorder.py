# -*- coding: utf-8 -*-
"""AdmitOR E3 -- heldout_workorder.py (v0.1)

Held-out work order: the NANO-CO problems that are not in the calibration
work order (zero token).

Purpose
    Writes a gate work order and a labels file for every NANO-CO problem
    whose id is not in the calibration work order. Ids follow the scheme of
    e3_calibrate.py workorder, e3_<problem_type>_<index>, so the held-out
    set and the calibration set are disjoint by id. No model is called.

Inputs
    --nano         nano-co.jsonl (one problem per line, with problem_type,
                   index, question and answer)
    --calibration  the calibration work order (e3_workorder.jsonl)
    --out          output work order, one {"sample_id", "question"} per line
    --labels       output labels file, one {"sample_id", "question",
                   "answer", "problem_type"} per line, the format of
                   e3_labels.jsonl

Outputs
    <out> and <labels>; a one-line JSON summary of the counts is printed.

Reproduce (from the repository root)
    python scripts/heldout_workorder.py \\
        --nano datasets/train_set/nano-co.jsonl \\
        --calibration <OptSkills>/outputs/e3/e3_workorder.jsonl \\
        --out outputs/heldout/heldout_workorder.jsonl \\
        --labels outputs/heldout/heldout_labels.jsonl
"""
from __future__ import annotations

import argparse
import json
import os


def main() -> None:
    ap = argparse.ArgumentParser(description="Work order of the NANO-CO problems outside the calibration set.")
    ap.add_argument("--nano", required=True)
    ap.add_argument("--calibration", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--labels", required=True)
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.nano, encoding="utf-8") if l.strip()]
    calib = [json.loads(l) for l in open(a.calibration, encoding="utf-8") if l.strip()]
    calib_ids = {str(r["sample_id"]) for r in calib}
    calib_q = {r["question"] for r in calib}

    ids = [f"e3_{r.get('problem_type', 'x')}_{r.get('index', i)}" for i, r in enumerate(rows, 1)]
    if len(set(ids)) != len(ids):
        raise SystemExit("ids of the NANO-CO file are not unique; no file written")

    picked = [(sid, r) for sid, r in zip(ids, rows) if sid not in calib_ids]
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(a.labels) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="\n") as wo, \
            open(a.labels, "w", encoding="utf-8", newline="\n") as lb:
        for sid, r in picked:
            wo.write(json.dumps({"sample_id": sid, "question": r["question"]}, ensure_ascii=False) + "\n")
            lb.write(json.dumps({"sample_id": sid, "question": r["question"], "answer": r.get("answer"),
                                 "problem_type": r.get("problem_type")}, ensure_ascii=False) + "\n")
    print(json.dumps({
        "nano_co": len(rows),
        "calibration": len(calib),
        "calibration_ids_found_in_nano_co": len(calib_ids & set(ids)),
        "heldout": len(picked),
        "heldout_ids_shared_with_calibration": len({s for s, _ in picked} & calib_ids),
        "heldout_questions_shared_with_calibration": sum(1 for _, r in picked if r["question"] in calib_q),
        "problem_types": len({r.get("problem_type") for _, r in picked}),
    }))


if __name__ == "__main__":
    main()
