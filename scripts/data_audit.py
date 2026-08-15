# -*- coding: utf-8 -*-
"""AdmitOR W1 data-hygiene audit: two checks.

Purpose
    1) Census: verify that each dataset holds the expected number of samples
       (the size fingerprint of the cleaned LLMOPT distribution).
    2) Overlap: hash every problem statement and intersect the mining pool
       (OptMATH-Train) against each evaluation benchmark. The required result
       is zero overlap. A non-empty intersection means the mined experience
       could carry evaluation problems, which would invalidate E1, so the
       audit is a hard gate before E0 runs.

Inputs
    --root  the OptSkills datasets directory. The DATASETS table below maps
            each dataset name to a glob relative to that root and to its
            expected deduplicated sample count. Both .json and .jsonl are
            supported. The problem-statement field name is auto-detected
            from TEXT_KEYS; add a key there if a dataset uses another name.

Outputs
    A census table and an overlap table on stdout, plus a final verdict line.
    Nothing is written to disk.

Example invocation (from the repository root)
    python scripts/data_audit.py --root ../OptSkills-main/datasets
"""
import argparse
import glob
import hashlib
import json
import os
import re

# ---- adjust these two blocks to the actual repository layout --------------
# dataset name -> (glob pattern relative to root, expected sample count or None)
# Expected counts: Mamo.C=211, IndustryOR=100. For the rest the count is taken
# from the repository or the paper; leave None until counted, then backfill
# the observed value and freeze it as the size fingerprint.
DATASETS = {
    "optmath_train": ("train_set/optmath-train-300.jsonl", 300),
    "optibench": ("benchmark/optibench.jsonl", 605),
    "mamo_c": ("benchmark/mamo_complex_test.jsonl", 211),
    "optmath_bench": ("benchmark/optmath_bench.jsonl", 166),
    "industryor": ("benchmark/industryor.jsonl", 100),
    "complexor": ("benchmark/complexor.jsonl", 18),
}
TEXT_KEYS = [
    "question",
    "problem",
    "description",
    "text",
    "prompt",
    "problem_description",
    "nl",
    "statement",
]
# ---------------------------------------------------------------------------


def norm(t: str) -> str:
    return re.sub(r"\s+", " ", (t or "").strip().lower())


def h(t: str) -> str:
    return hashlib.sha256(norm(t).encode("utf-8")).hexdigest()[:16]


def extract_text(rec):
    if isinstance(rec, str):
        return rec
    if isinstance(rec, dict):
        for k in TEXT_KEYS:
            if k in rec and isinstance(rec[k], str) and rec[k].strip():
                return rec[k]
    return None


def load_records(path):
    out = []
    try:
        if path.endswith(".jsonl"):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        out.append(json.loads(line))
        elif path.endswith(".json"):
            data = json.load(open(path, encoding="utf-8"))
            if isinstance(data, list):
                out.extend(data)
            elif isinstance(data, dict):
                for v in data.values():
                    if isinstance(v, list):
                        out.extend(v)
    except Exception as e:
        print(f"  [warn] failed to read {path}: {e}")
    return out


def collect(root, pattern):
    files = [
        p
        for p in glob.glob(os.path.join(root, pattern), recursive=True)
        if os.path.isfile(p) and p.endswith((".json", ".jsonl"))
    ]
    hashes, miss = {}, 0
    for p in files:
        for rec in load_records(p):
            t = extract_text(rec)
            if t is None:
                miss += 1
            else:
                hashes.setdefault(h(t), t[:60])
    return files, hashes, miss


def main():
    ap = argparse.ArgumentParser(
        description="Census and mining-pool overlap audit over the benchmark " "datasets."
    )
    ap.add_argument("--root", required=True, help="OptSkills datasets directory")
    args = ap.parse_args()

    print(f"root = {args.root}\n")
    got = {}
    print("== census ==============================")
    for name, (pat, expect) in DATASETS.items():
        files, hashes, miss = collect(args.root, pat)
        got[name] = hashes
        exp = (
            f"expected {expect}"
            if expect
            else "expected: undetermined (backfill and freeze after counting)"
        )
        flag = ""
        if expect is not None and len(hashes) != expect:
            flag = "  <-- count mismatch, check this is the cleaned " "LLMOPT distribution"
        print(
            f"  {name:14s} {len(files):3d} file(s), "
            f"{len(hashes):4d} deduplicated statement(s) ({exp}){flag}"
        )
        if miss:
            print(
                f"      [warn] {miss} record(s) had no recognized "
                f"statement field; add the correct key to TEXT_KEYS"
            )

    print("\n== overlap (mining pool vs each benchmark, must be all zero) ==")
    train = set(got.get("optmath_train", {}))
    clean = True
    for name in DATASETS:
        if name == "optmath_train":
            continue
        inter = train & set(got.get(name, {}))
        status = "OK" if not inter else f"found {len(inter)} overlapping row(s)"
        if inter:
            clean = False
            for k in list(inter)[:3]:
                print(f"      overlap sample: {got[name][k]}...")
        print(f"  train INTERSECT {name:14s}: {status}")
    print(
        "\nverdict: "
        + (
            "overlap audit passed, record it in the runlog for the audit trail."
            if clean
            else "overlap found -- stop and resolve it before running E0."
        )
    )


if __name__ == "__main__":
    main()
