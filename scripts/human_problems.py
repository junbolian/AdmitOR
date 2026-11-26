# -*- coding: utf-8 -*-
"""Problem files of the runs on human-written texts (no model call, no key).

Purpose
    Build the problem file (`workorder.jsonl`: one {"sample_id", "question"} per line, the text given to the
    models) and `problems.csv` (identifier, source record, label) of the four benchmarks of
    artifacts/v2/humanbench and artifacts/v2/optimind.

Inputs
    datasets/benchmark/industryor.jsonl, datasets/benchmark/mamo_complex_test.jsonl
        published releases of IndustryOR (100) and Mamo ComplexLP (211), as distributed by the OptSkills host.
        sample_id = industryor_<index> / mamo_complex_<index>; the label is the field `answer`.
    datasets/optimind_corrected/optimind_cleaned_classified_industryor.csv,
    datasets/optimind_corrected/optimind_cleaned_classified_mamo_complex.csv
        corrected releases by the OptiMind authors (99 and 210 rows; see datasets/optimind_corrected/SOURCE.md).
        sample_id = om_industryor_<row> / om_mamo_<row>, <row> the 0-based CSV row. The `answer` column holds a
        number (IndustryOR) or a one-element JSON list (Mamo); the number is the label, and a whole number written
        with a zero decimal (for example 219816.0, the float formatting of the CSV) is stored as an integer.
        `problem_class` is kept in problems.csv.

Outputs (under --out, default artifacts/v2)
    humanbench/industryor/, humanbench/mamo_complex/   workorder.jsonl, problems.csv (sample_id, source_record, label)
    optimind/industryor/, optimind/mamo_complex/       workorder.jsonl, problems.csv (sample_id, source_row, label,
                                                       problem_class)
    The SHA-256 of each workorder.jsonl is printed.

Usage (from the repository root)
    python scripts/human_problems.py [--out artifacts/v2]
"""
import argparse
import csv
import hashlib
import json
import os

ap = argparse.ArgumentParser(description="Problem files of the runs on human-written texts.")
ap.add_argument("--out", default=os.path.join("artifacts", "v2"))
ap.add_argument("--datasets", default="datasets")
A = ap.parse_args()
csv.field_size_limit(2 ** 31 - 1)


def label_number(a):
    v = json.loads(a.strip())
    if isinstance(v, list):
        if len(v) != 1:
            raise SystemExit("answer is not a one-element list: %r" % a)
        v = v[0]
    v = float(v)
    return int(v) if v.is_integer() else v


def write(folder, wo, header, rows):
    os.makedirs(folder, exist_ok=True)
    text = "".join(json.dumps({"sample_id": s, "question": q}, ensure_ascii=False) + "\n" for s, q in wo)
    open(os.path.join(folder, "workorder.jsonl"), "w", encoding="utf-8", newline="\n").write(text)
    with open(os.path.join(folder, "problems.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    print("%s: %d problems, workorder.jsonl SHA-256 %s" % (folder, len(wo), hashlib.sha256(text.encode("utf-8")).hexdigest()))


for bench, src in (("industryor", "industryor.jsonl"), ("mamo_complex", "mamo_complex_test.jsonl")):
    recs = [json.loads(l) for l in open(os.path.join(A.datasets, "benchmark", src), encoding="utf-8") if l.strip()]
    ids = ["%s_%s" % (bench, r["index"]) for r in recs]
    write(os.path.join(A.out, "humanbench", bench), [(s, r["question"]) for s, r in zip(ids, recs)],
          ["sample_id", "source_record", "label"], [[s, r["index"], json.dumps(r["answer"])] for s, r in zip(ids, recs)])

for bench, pre, src in (("industryor", "om_industryor_", "optimind_cleaned_classified_industryor.csv"),
                        ("mamo_complex", "om_mamo_", "optimind_cleaned_classified_mamo_complex.csv")):
    rows = list(csv.DictReader(open(os.path.join(A.datasets, "optimind_corrected", src), encoding="utf-8-sig", newline="")))
    ids = [pre + str(i) for i in range(len(rows))]
    write(os.path.join(A.out, "optimind", bench), [(s, r["question"]) for s, r in zip(ids, rows)],
          ["sample_id", "source_row", "label", "problem_class"],
          [[s, i, json.dumps(label_number(r["answer"])), r["problem_class"]] for i, (s, r) in enumerate(zip(ids, rows))])
