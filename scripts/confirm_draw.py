# -*- coding: utf-8 -*-
"""Draw of the confirmatory OptMATH-200 sample (no model call).

Purpose
    The first OptMATH sample (OptMATH-295, shipped as datasets/train_set/optmath-train-300.jsonl) is
    random.Random(42).sample(range(201071), 300) of the lines of OptMATH-Train.jsonl. The confirmatory
    sample is drawn from the records outside it: every line of OptMATH-Train.jsonl whose 0-based line
    number is not a `source_index` of the first sample, that parses as JSON, has a non-empty question and
    a finite numeric answer (200,771 records). The pool, sorted by line number, is sampled with
    random.Random(42).sample(pool, 200); the drawn order is kept.

Inputs
    --optmath-train  OptMATH-Train.jsonl of the Hugging Face dataset shushulei/OptMATH-Train
                     (201,071 lines; SHA-256 0abc84605a44cad50b2e14a9ec18df96141b95f9cf56bd8e2630eb8cdf71d0ed)
    --first-sample   datasets/train_set/optmath-train-300.jsonl (default)
    --out            output directory

Outputs (in --out)
    ids.json          the 200 drawn line numbers, in drawn order
    ids.sha256        SHA-256 of ids.json
    workorder.jsonl   {"sample_id": "conf_<line>", "sample_key": "<line>", "question": ...} per problem
    labels.jsonl      {"sample_id", "source_index", "answer"} per problem (not read by certification)
    The question is the record's `input` without the leading "# Question:" and the trailing
    "\n\n# Note:" block, stripped.

Usage (from the repository root)
    python scripts/confirm_draw.py --optmath-train <OptMATH-Train.jsonl> --out <dir>
"""
import argparse
import hashlib
import json
import math
import os
import random


def question(inp):
    t = inp[len("# Question:"):] if inp.startswith("# Question:") else inp
    k = t.find("\n\n# Note:")
    if k >= 0:
        t = t[:k]
    return t.strip()


def numeric(a):
    if isinstance(a, bool) or a is None:
        return False
    try:
        x = float(a)
    except (TypeError, ValueError):
        return False
    return math.isfinite(x)


def main():
    ap = argparse.ArgumentParser(description="Draw of the confirmatory OptMATH-200 sample.")
    ap.add_argument("--optmath-train", required=True)
    ap.add_argument("--first-sample", default=os.path.join("datasets", "train_set", "optmath-train-300.jsonl"))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    first = {int(json.loads(l)["source_index"]) for l in open(a.first_sample, encoding="utf-8") if l.strip()}
    pool, lines, bad, no_q, no_a = [], 0, 0, 0, 0
    with open(a.optmath_train, encoding="utf-8") as f:
        for i, l in enumerate(f):
            lines += 1
            if i in first:
                continue
            try:
                r = json.loads(l)
            except ValueError:
                bad += 1
                continue
            if not question(r.get("input") or ""):
                no_q += 1
                continue
            if not numeric(r.get("answer")):
                no_a += 1
                continue
            pool.append(i)
    pool.sort()
    ids = random.Random(42).sample(pool, 200)
    os.makedirs(a.out, exist_ok=True)
    p = os.path.join(a.out, "ids.json")
    json.dump(ids, open(p, "w", encoding="utf-8"))
    digest = hashlib.sha256(open(p, "rb").read()).hexdigest()
    open(os.path.join(a.out, "ids.sha256"), "w", encoding="utf-8", newline="\n").write("%s  ids.json\n" % digest)
    need = set(ids)
    rec = {}
    with open(a.optmath_train, encoding="utf-8") as f:
        for i, l in enumerate(f):
            if i in need:
                rec[i] = json.loads(l)
    with open(os.path.join(a.out, "workorder.jsonl"), "w", encoding="utf-8", newline="\n") as w, \
            open(os.path.join(a.out, "labels.jsonl"), "w", encoding="utf-8", newline="\n") as lab:
        for i in ids:
            sid = "conf_%d" % i
            w.write(json.dumps({"sample_id": sid, "sample_key": str(i), "question": question(rec[i]["input"])}, ensure_ascii=False) + "\n")
            lab.write(json.dumps({"sample_id": sid, "source_index": i, "answer": str(rec[i]["answer"])}) + "\n")
    print(json.dumps({"lines": lines, "first_sample": len(first), "unparseable": bad, "empty_question": no_q,
                      "non_numeric_answer": no_a, "pool": len(pool), "drawn": len(ids), "ids_sha256": digest,
                      "overlap_with_first_sample": len(set(ids) & first)}))


if __name__ == "__main__":
    main()
