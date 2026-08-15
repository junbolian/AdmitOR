"""AdmitOR E1 -- e1_relabel.py (v0.1)

Per-arm replay over a shared collect run (OptSkills --phase cluster
trajectories). Candidates and solve logs are generated ONCE; each judge
re-decides admission offline by rewriting the row's ground truth to the
arm's effective value, so the unmodified host machinery reproduces the
arm's verdicts during library rebuild.

Inputs
    --collect       the shared collect run's trajectories.jsonl
    --arm           one of gt, vote, runsok, gate
    --labels        original labeled jsonl, required for --arm gt
    --verdicts-dir  directory of <sample_id>.json verdicts, required for
                    --arm gate
    --out           output path for the arm's relabeled trajectories
    --work-order    optional output path for the gate arm's list of
                    uncertified samples

Outputs
    <out>                    the arm's relabeled trajectories jsonl
    <out>.summary.json       per-arm counts, also echoed to stdout
    <work-order>             if given with --arm gate

This step costs no tokens: it is a pure offline relabeling of logs that
already exist.

Usage (run from the repository root; paths may be relative):
  python scripts/e1_relabel.py --collect <trajectories.jsonl> --arm gt \
      --labels <original labeled jsonl> --out <arm trajectories.jsonl>
  python scripts/e1_relabel.py --collect ... --arm vote   --out ...
  python scripts/e1_relabel.py --collect ... --arm runsok --out ...
  python scripts/e1_relabel.py --collect ... --arm gate \
      --verdicts-dir <dir of <sample_id>.json> --out ... \
      [--work-order <missing-certifications jsonl>]

Output rows are byte-identical to the input except:
  answer            <- arm's effective ground truth
  eligible          <- any candidate positive under the arm
  e1_arm            <- arm name
  e1_answer_source  <- provenance tag
  e1_original_answer<- input row's answer field (audit trail)
Summary (stdout + <out>.summary.json): per-arm positives, eligibility,
dev-split exclusions, gate work-order size.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from label_oracle import (
    DEV_SPLIT_INDICES,
    NO_CONSENSUS,
    attach_metrics,
    host_label,
    make_oracle,
    row_candidates,
    row_index,
)

SOURCE = {
    "gt": "vault_published_labels",
    "vote": "candidate_majority_2dp",
    "runsok": "empty_gt_success_rule",
    "gate": "admitor_certificate",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collect", required=True)
    ap.add_argument("--arm", required=True, choices=["gt", "vote", "runsok", "gate"])
    ap.add_argument("--labels", default="")
    ap.add_argument("--verdicts-dir", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--work-order", default="")
    a = ap.parse_args()

    if a.arm == "gt" and not a.labels:
        ap.error("--arm gt requires --labels (original labeled jsonl)")
    if a.arm == "gate" and not a.verdicts_dir:
        ap.error("--arm gate requires --verdicts-dir")

    oracle = make_oracle(a.arm, labels_path=a.labels, verdicts_dir=a.verdicts_dir)

    n_rows = n_eligible = n_dev = 0
    pos = neg = no_cons = 0
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.collect, encoding="utf-8") as fin, open(a.out, "w", encoding="utf-8") as fout:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            n_rows += 1
            idx = row_index(row)
            if idx in DEV_SPLIT_INDICES:
                n_dev += 1
            gt = oracle.effective_gt(row)
            cands = row_candidates(row)
            for c in cands:
                c["objective_metrics"] = attach_metrics(c, gt)
            labels = [host_label(c, gt) for c in cands]
            pos += sum(1 for l in labels if l == "positive")
            neg += sum(1 for l in labels if l == "negative")
            if gt == NO_CONSENSUS:
                no_cons += 1
            eligible = any(l == "positive" for l in labels)
            n_eligible += int(eligible)
            row["e1_original_answer"] = row.get("answer", "")
            row["answer"] = gt
            row["eligible"] = eligible
            row["e1_arm"] = a.arm
            row["e1_answer_source"] = SOURCE[a.arm]
            fout.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "arm": a.arm,
        "rows": n_rows,
        "eligible": n_eligible,
        "candidates_positive": pos,
        "candidates_negative": neg,
        "no_consensus_rows": no_cons,
        "dev_split_rows_present": n_dev,
        "note": "dev-split rows (indices 1-5) are excluded from E1 "
        "accounting downstream; they are relabeled here unchanged "
        "for pipeline uniformity",
    }
    if a.arm == "gate":
        summary["missing_certifications"] = len(oracle.work_order)
        if a.work_order:
            os.makedirs(os.path.dirname(os.path.abspath(a.work_order)), exist_ok=True)
            with open(a.work_order, "w", encoding="utf-8") as f:
                for rec in oracle.work_order:
                    f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with open(a.out + ".summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
