# -*- coding: utf-8 -*-
"""Per-problem status of the published IndustryOR and Mamo ComplexLP texts under the expert audit of Xiao et al. (2025)
(no model call, no key).

Purpose
    Match every problem of artifacts/v2/humanbench to the cleaned files of the expert audit and record whether the
    audit removed it, kept it with the same label, or kept it with a changed label. The result is
    artifacts/v2/humanbench/expert/expert_status.csv, which scripts/human_tables.py reads for table h5.

Inputs
    --expert   a folder with the four files of the expert audit, downloaded as listed in
               artifacts/v2/humanbench/expert/SOURCE.md (address, commit, SHA-256) and stored under the local paths given
               there: clean/IndustryOR.jsonl, clean/Mamo/Mamo_complex_lp_clean.jsonl, original/IndustryOR/dataset.jsonl,
               original/Mamo/data/optimization/Complex_LP/mamo_complex_lp.jsonl. These files are not redistributed here.
    --records  artifacts/v2/humanbench (default): <bench>/workorder.jsonl and <bench>/problems.csv

Rule
    A problem is matched to the cleaned file by question text after lowercasing and collapsing whitespace. With an exact
    match its status is "kept, same label" or "kept, label changed" (numeric comparison with relative tolerance 1e-9);
    without one it counts as "removed", and the best word 5-gram Jaccard similarity to any cleaned record is recorded.

Output
    --out (default <records>/expert/expert_status.csv): benchmark, sample_id, expert_status, original_label, expert_label,
    match_to_cleaned_file, best_5gram_jaccard_to_cleaned_file, exact_match_in_original_expert_file

Usage (from the repository root)
    python scripts/human_expert_status.py --expert <folder> [--records artifacts/v2/humanbench] [--out ...]
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_eval import to_num  # noqa: E402

ap = argparse.ArgumentParser(description="Expert-audit status of the published IndustryOR and Mamo ComplexLP texts.")
ap.add_argument("--expert", required=True)
ap.add_argument("--records", default=os.path.join("artifacts", "v2", "humanbench"))
ap.add_argument("--out", default=None)
A = ap.parse_args()
OUT = A.out or os.path.join(A.records, "expert", "expert_status.csv")
NAME = {"industryor": "IndustryOR", "mamo_complex": "Mamo ComplexLP"}
EXP = {"industryor": ("original/IndustryOR/dataset.jsonl", "clean/IndustryOR.jsonl", "en_question", "en_answer"),
       "mamo_complex": ("original/Mamo/data/optimization/Complex_LP/mamo_complex_lp.jsonl", "clean/Mamo/Mamo_complex_lp_clean.jsonl",
                        "Question", "Answer")}
SHA = {"clean/IndustryOR.jsonl": "d7c2c05377ade5bc6a401ebf3075f0e00fa91068439761e5b46fa3045ffc19b5",
       "clean/Mamo/Mamo_complex_lp_clean.jsonl": "28e10dff1146ff635673293b5730abb3d7efa2f7bbe91de60fe67b729dfe7a0d",
       "original/IndustryOR/dataset.jsonl": "4c7f8db266f2f4ccc3d4784fc754ae1ab195226880c9b19b97b67b655fa47752",
       "original/Mamo/data/optimization/Complex_LP/mamo_complex_lp.jsonl": "07eb3db3d2af099871dfa4425b14887775179c158c38944fe4fe152b615bbfc3"}


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def norm(t):
    return re.sub(r"\s+", " ", (t or "").lower()).strip()


def grams(t):
    w = norm(t).split(" ")
    return {tuple(w[i:i + 5]) for i in range(len(w) - 4)}


def same_label(a, b):
    x, y = to_num(a), to_num(b)
    if x is None or y is None:
        return str(a).strip() == str(b).strip()
    return abs(x - y) <= 1e-9 * max(1.0, abs(x), abs(y))


for rel, h in SHA.items():
    p = os.path.join(A.expert, *rel.split("/"))
    got = hashlib.sha256(open(p, "rb").read()).hexdigest()
    if got != h:
        sys.exit("SHA-256 of %s is %s, expected %s (see expert/SOURCE.md)" % (rel, got, h))
rows = []
for b in ("industryor", "mamo_complex"):
    q = {r["sample_id"]: r["question"] for r in jl(os.path.join(A.records, b, "workorder.jsonl"))}
    lab = {r["sample_id"]: json.loads(r["label"]) for r in csv.DictReader(open(os.path.join(A.records, b, "problems.csv"), encoding="utf-8"))}
    orig, clean, qk, ak = EXP[b]
    O = jl(os.path.join(A.expert, *orig.split("/")))
    C = jl(os.path.join(A.expert, *clean.split("/")))
    Cn = {norm(r[qk]): r for r in C}
    On = {norm(r[qk]): r for r in O}
    Cg = [grams(r[qk]) for r in C]
    for sid, text in q.items():
        n = norm(text)
        if n in Cn:
            new = Cn[n][ak]
            st, el, match, best = ("kept, same label" if same_label(new, lab[sid]) else "kept, label changed"), new, "exact", 1.0
        else:
            g = grams(text)
            best = max((len(g & x) / len(g | x) if g and x else 0.0 for x in Cg), default=0.0)
            st, el, match, best = "removed", None, "no exact match", round(best, 4)
        rows.append([NAME[b], sid, st, lab[sid], "" if el is None else el, match, best, n in On])
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh, lineterminator="\n")
    w.writerow(["benchmark", "sample_id", "expert_status", "original_label", "expert_label", "match_to_cleaned_file",
                "best_5gram_jaccard_to_cleaned_file", "exact_match_in_original_expert_file"])
    w.writerows(rows)
print("wrote %s: %d problems" % (OUT, len(rows)))
