# -*- coding: utf-8 -*-
"""Poison-file provenance and retrieval impact (zero token).

Purpose
    1. Classify a named library file as two-family-only, mixed, or
       three-family-only under the tau counterfactual.
    2. For every poison-bearing file, list the problem ids of the poison
       admissions it holds and whether each problem is tau-admitted or
       two-family.
    3. From the gate arm's eval trajectories, count retrievals of the
       poison-bearing and two-family-only files per plate, and compare
       round-aware accuracy of items that retrieved one against items that
       did not.

Inputs (all required on the command line)
    --arm            <host>/outputs/e1/arms/gate.jsonl (private, not distributed)
    --runs           artifacts/e1/certify_runs (in git)
    --vault          datasets/vault/optmath-train-300-labels.jsonl (in git)
    --build-summary  artifacts/e1/libraries/skill_library_gate.build_summary.json (in git)
    --admitted       release/reviewer_round/admitted_ids_wild_138.txt (in git)
    --eval-root      <host>/outputs/e1/eval, uses the gate arm
                     (private, not distributed)
    --named          library file title to classify (item 1)
    --out            output directory

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

Reproduce (from the repository root)
    python scripts/poison_provenance.py --arm <host>/outputs/e1/arms/gate.jsonl --runs artifacts/e1/certify_runs --vault datasets/vault/optmath-train-300-labels.jsonl --build-summary artifacts/e1/libraries/skill_library_gate.build_summary.json --admitted release/reviewer_round/admitted_ids_wild_138.txt --eval-root <host>/outputs/e1/eval --out reanalysis/reviewer_round

Outputs
    <out>/03_0_poison_provenance.md

Paper location
    Section 4.2 (27 problems / 69 candidates / 8 poisoned) and Appendix C
    (11 poison-bearing files).
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))  # repository root, for admitor/
from label_oracle import DEV_SPLIT_INDICES, host_label, row_candidates  # noqa: E402
from score_eval import round_aware, to_num  # noqa: E402

DEV = {"sample_%d" % i for i in DEV_SPLIT_INDICES}
PLATES = ["complexor", "industryor", "mamo_c", "optmath", "optibench"]


def fam_span_map(runs):
    out = {}
    for d in sorted(os.listdir(runs)):
        p = os.path.join(runs, d, "verdict_full.json")
        if os.path.isfile(p):
            v = json.load(open(p, encoding="utf-8"))
            out[d] = len({str(m)[:1] for m in (v.get("clique") or [])})
    return out


def main():
    ap = argparse.ArgumentParser(description="Poison provenance and retrieval.")
    for f in ("arm", "runs", "vault", "build_summary", "admitted", "eval_root", "out"):
        ap.add_argument("--" + f.replace("_", "-"), dest=f, required=True)
    ap.add_argument("--named", default="Bin Packing with Resource Activation")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    vault = {}
    for line in open(a.vault, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            vault["sample_%s" % r["idx"]] = str(r.get("answer"))
    span = fam_span_map(a.runs)
    admitted138 = {l.strip() for l in open(a.admitted, encoding="utf-8") if l.strip()}

    # candidate-level poison, keyed as sample_key__candidate_id
    poison_keys, two_fam_samples, key_to_sid = {}, set(), {}
    for line in open(a.arm, encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        sid = str(row.get("sample_id"))
        if sid in DEV or not row.get("eligible"):
            continue
        if span.get(sid) == 2:
            two_fam_samples.add(str(row.get("sample_key")))
        gt, ans = str(row.get("answer", "")), vault.get(sid)
        for c in row_candidates(row):
            if host_label(c, gt) != "positive":
                continue
            ck = "%s__%s" % (row.get("sample_key"), c.get("candidate_id"))
            key_to_sid[ck] = sid
            if ans is None or host_label(c, ans) != "positive":
                poison_keys[ck] = sid

    b = json.load(open(a.build_summary, encoding="utf-8"))
    clusters = (b.get("build_summary") or {}).get("clusters") or []

    file_class, file_poison = {}, collections.defaultdict(list)
    for cl in clusters:
        path = (cl.get("record") or {}).get("path")
        name = (cl.get("record") or {}).get("name")
        keys = [str(k) for k in (cl.get("sample_keys") or [])]
        if not path or not keys:
            continue
        n2 = sum(1 for k in keys if k in two_fam_samples)
        file_class[path] = (
            "two-family-only" if n2 == len(keys) else
            "mixed" if n2 else "three-family-only", name, len(keys), n2)
        for ca in (cl.get("candidate_analyses") or []):
            ck = ca.get("candidate_id")
            if ck in poison_keys:
                file_poison[path].append(poison_keys[ck])

    L = []

    def w(s=""):
        L.append(s)

    w("# Poison-file provenance and retrieval impact")
    w()
    w("Zero-token. Generated by `admitor-infra/poison_provenance.py`.")
    w()

    # ---- item 1 ----
    w("## 1. The appendix example file")
    w()
    hit = [(p, v) for p, v in file_class.items() if v[1] == a.named]
    if not hit:
        hit = [(p, v) for p, v in file_class.items()
               if a.named.lower().replace(" ", "_") in p.lower()]
    if hit:
        p, (cls, name, nk, n2) = hit[0]
        w("| Field | Value |")
        w("|---|---|")
        w("| title | %s |" % name)
        w("| file | `%s` |" % p)
        w("| cluster members (sample_keys) | %d |" % nk)
        w("| of which two-family-admitted | %d |" % n2)
        w("| class | **%s** |" % cls)
        w("| survives tau >= 33.3 | **%s** |" % ("no" if cls == "two-family-only" else "yes"))
    else:
        w("No library file titled `%s` found in the build summary." % a.named)
    w()

    # ---- item 2 ----
    w("## 2. Poison-bearing files, problem by problem")
    w()
    w("The per-sample K3 attribution (class b, d-missing, d-truncated) is "
      "**not recorded in any artifact**: the 22 review packets under "
      "`outputs/e3/review/` carry unticked `[ ] (a) / (b) / (c)` boxes (0 of 22 "
      "ticked) and `wrong_admission_detail` has no class field. The class "
      "column below is therefore left as `not recorded`.")
    w()
    w("| File | class | poison | problem ids | tau-admitted | two-family | K3 class |")
    w("|---|---|---:|---|---|---|---|")
    for p in sorted(file_poison, key=lambda x: -len(file_poison[x])):
        sids = sorted(set(file_poison[p]), key=lambda s: int(s.split("_")[1]))
        tau = [s for s in sids if s in admitted138]
        twof = [s for s in sids if span.get(s) == 2]
        w("| `%s` | %s | %d | %s | %s | %s | not recorded |"
          % (p, file_class.get(p, ("?",))[0], len(file_poison[p]),
             ", ".join(sids), ", ".join(tau) or "-", ", ".join(twof) or "-"))
    w()

    # ---- item 3 ----
    w("## 3. Retrieval of poison-bearing and two-family-only files (gate arm)")
    w()
    poison_files = set(file_poison)
    only2_files = {p for p, v in file_class.items() if v[0] == "two-family-only"}
    w("Skill ids are recorded in the eval trajectories as "
      "`skill_selection.skill_id`; the library file name is `<skill_id>.md`.")
    w()
    w("| Plate | items | retrieved a poison-bearing file | retrieved a two-family-only file |")
    w("|---|---:|---:|---:|")
    detail = {}
    for plate in PLATES:
        fp = os.path.join(a.eval_root, "gate", plate, "trajectories.jsonl")
        if not os.path.isfile(fp):
            continue
        rows = []
        for line in open(fp, encoding="utf-8"):
            if not line.strip():
                continue
            r = json.loads(line)
            ss = r.get("skill_selection") or {}
            sk = ss.get("skill_id") if isinstance(ss, dict) else None
            fname = ("%s.md" % sk) if sk else None
            ok = round_aware(to_num(r.get("prediction")), to_num(r.get("answer")),
                             r.get("answer"))
            rows.append((fname, ok))
        detail[plate] = rows
        w("| %s | %d | %d | %d |"
          % (plate, len(rows),
             sum(1 for f, _ in rows if f in poison_files),
             sum(1 for f, _ in rows if f in only2_files)))
    w()
    w("Round-aware accuracy, items that retrieved a poison-bearing file "
      "against items that did not:")
    w()
    w("| Plate | retrieved poison-bearing: n | acc | did not: n | acc |")
    w("|---|---:|---:|---:|---:|")
    for plate, rows in detail.items():
        ry = [ok for f, ok in rows if f in poison_files]
        rn = [ok for f, ok in rows if f not in poison_files]
        w("| %s | %d | %s | %d | %s |"
          % (plate, len(ry),
             "%.2f" % (100.0 * sum(ry) / len(ry)) if ry else "-",
             len(rn), "%.2f" % (100.0 * sum(rn) / len(rn)) if rn else "-"))
    w()
    w("| Plate | retrieved two-family-only: n | acc | did not: n | acc |")
    w("|---|---:|---:|---:|---:|")
    for plate, rows in detail.items():
        ry = [ok for f, ok in rows if f in only2_files]
        rn = [ok for f, ok in rows if f not in only2_files]
        w("| %s | %d | %s | %d | %s |"
          % (plate, len(ry),
             "%.2f" % (100.0 * sum(ry) / len(ry)) if ry else "-",
             len(rn), "%.2f" % (100.0 * sum(rn) / len(rn)) if rn else "-"))
    w()
    allrows = [r for rows in detail.values() for r in rows]
    for label, S in (("poison-bearing", poison_files), ("two-family-only", only2_files)):
        ry = [ok for f, ok in allrows if f in S]
        rn = [ok for f, ok in allrows if f not in S]
        w("Pooled, %s: retrieved n=%d acc=%.2f; not retrieved n=%d acc=%.2f"
          % (label, len(ry), 100.0 * sum(ry) / len(ry) if ry else float("nan"),
             len(rn), 100.0 * sum(rn) / len(rn) if rn else float("nan")))
        w()

    p = os.path.join(a.out, "03_0_poison_provenance.md")
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("wrote", p)
    print("named file class:", hit[0][1][0] if hit else "NOT FOUND")
    print("poison-bearing files:", len(file_poison), " two-family-only:", len(only2_files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
