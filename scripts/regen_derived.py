# -*- coding: utf-8 -*-
"""AdmitOR -- regen_derived.py

Purpose
    Deterministically regenerate the two derived files that the experiments
    need but that this repository deliberately does not ship, because both
    contain third-party benchmark content:

      1. the blind mining file, which is OptMATH-Train with the answer field
         removed. E1 mines experience from it, and the gate must never see
         the answers, which is the whole point of the label-free setting.
      2. the sealed vault label file, which is the answer column of the same
         dataset keyed by index. It is used only after the fact, to grade
         admissions in E3.

    Both are pure functions of one upstream file, so anyone with the original
    dataset can rebuild them byte for byte. The expected sha256 of each output
    is checked against the fingerprints recorded below, which is what lets a
    third party confirm they rebuilt exactly the files the paper used.

Inputs
    --source  path to the original OptMATH-Train 300 jsonl, as distributed
              with the OptSkills host under datasets/train_set/. This file is
              third-party data and is not redistributed here.
    --out-dir output directory for the regenerated files
              (default data/derived, which is gitignored)

Outputs
    <out-dir>/optmath-train-300-blind.jsonl        index, source_index, question
    <out-dir>/optmath-train-300-labels.jsonl       idx, answer
    A verification table on stdout with the sha256 of each output and whether
    it matches the recorded fingerprint. Exit code is non-zero on mismatch.

Example invocation (from the repository root)
    python scripts/regen_derived.py \\
        --source ../OptSkills-main/datasets/train_set/optmath-train-300.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

# sha256 of the exact derived files used for every number in the paper.
# A mismatch means the source dataset is not the same revision we mined.
FINGERPRINTS = {
    "optmath-train-300-blind.jsonl": "48bb45321f977d5a883eb70979afa68733565cd417857ee0277e2617941e0a2b",
    "optmath-train-300-labels.jsonl": "c05faaa8777e04cdd61eb29239c1b5b14e5d227d8ae46a7cf5c5881b3357c155",
}

# sha256 of the upstream source file these were derived from, as shipped with
# the OptSkills host at the commit recorded in patches/README.md. Reported for
# provenance; a mismatch here is a warning, the output fingerprints above are
# the actual gate.
SOURCE_FINGERPRINT = "bc7ee68d07c2300bbd62ce77ca5d2c76e553aa393bee72e4a2f35afe1a656535"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_source(path: str) -> list:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    if not rows:
        raise SystemExit(f"[regen] source file is empty: {path}")
    missing = [k for k in ("index", "question", "answer") if k not in rows[0]]
    if missing:
        raise SystemExit(
            f"[regen] source rows lack required field(s) {missing}; point "
            f"--source at the original OptMATH-Train 300 jsonl shipped with "
            f"the OptSkills host"
        )
    return rows


def _write_jsonl(records: list, path: str) -> None:
    """Write one compact JSON object per line.

    Two byte-level details of the original files are reproduced deliberately,
    because the recorded fingerprints do not match without them: records are
    separated by CRLF, and there is no trailing newline after the final
    record. newline="" disables newline translation so the separator is
    written literally on every platform.
    """
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("\r\n".join(json.dumps(r, ensure_ascii=False) for r in records))


def write_blind(rows: list, path: str) -> None:
    """OptMATH-Train with the answer column dropped. Key order and row order
    follow the source exactly so the output is byte-reproducible."""
    _write_jsonl(
        [
            {"index": r["index"], "source_index": r.get("source_index"), "question": r["question"]}
            for r in rows
        ],
        path,
    )


def write_labels(rows: list, path: str) -> None:
    """The sealed vault: index and answer only, no problem text."""
    _write_jsonl([{"idx": r["index"], "answer": r["answer"]} for r in rows], path)


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Regenerate the derived blind mining file and vault "
        "label file from the original benchmark dataset."
    )
    ap.add_argument(
        "--source",
        required=True,
        help="original OptMATH-Train 300 jsonl (third-party, not "
        "redistributed by this repository)",
    )
    ap.add_argument(
        "--out-dir",
        default=os.path.join("data", "derived"),
        help="output directory (default data/derived)",
    )
    a = ap.parse_args()

    rows = load_source(a.source)
    os.makedirs(a.out_dir, exist_ok=True)
    src_hash = sha256_file(a.source)
    print(f"[regen] source: {a.source}")
    print(f"[regen] source sha256: {src_hash}")
    if src_hash != SOURCE_FINGERPRINT:
        print(
            f"[regen] note: source differs from the revision we mined "
            f"(expected {SOURCE_FINGERPRINT}); the output check below is "
            f"what decides comparability"
        )
    print(f"[regen] {len(rows)} record(s) read\n")

    blind = os.path.join(a.out_dir, "optmath-train-300-blind.jsonl")
    labels = os.path.join(a.out_dir, "optmath-train-300-labels.jsonl")
    write_blind(rows, blind)
    write_labels(rows, labels)

    ok = True
    print(f"{'file':38s} {'status':8s} sha256")
    print("-" * 110)
    for path in (blind, labels):
        name = os.path.basename(path)
        got = sha256_file(path)
        want = FINGERPRINTS[name]
        match = got == want
        ok &= match
        print(f"{name:38s} {'MATCH' if match else 'DIFFERS':8s} {got}")
        if not match:
            print(f"{'':38s} {'expected':8s} {want}")
    print("-" * 110)
    if ok:
        print("[regen] all outputs match the fingerprints used in the paper.")
        return 0
    print(
        "[regen] FINGERPRINT MISMATCH: the source dataset is not the "
        "revision the paper mined, or its row order differs. Results "
        "derived from these files will not be comparable to the paper."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
