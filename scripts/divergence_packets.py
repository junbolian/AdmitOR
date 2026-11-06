# -*- coding: utf-8 -*-
"""Case packets for the problems in which resampling separated candidates
that agree at the stated instance (zero token, read only).

For each listed problem the packet holds: the problem text, the withheld
label, every candidate's value and solver status on each instance, the
sampled parameter values of each instance, the extracted specification
(base values and perturbation domains), and each candidate's program.
The packets carry no judgement; classification is done by reading them.

Inputs
    --runs-full  certify run directory of the run records, one folder per
                 problem with verdict_full.json, spec.json and the candidate
                 programs (<candidate id>.py)
    --stream     datasets/train_set/optmath-train-300-blind.jsonl (in git)
    --vault      datasets/vault/optmath-train-300-labels.jsonl (in git)
    --samples    comma-separated sample ids
    --out        default outputs/additional_2026-11/divergence_packets
"""
from __future__ import annotations

import argparse
import json
import os

DEFAULT = ("sample_20,sample_28,sample_81,sample_93,sample_147,sample_165,"
           "sample_267,sample_17,sample_140,sample_288")


def short(x, nd=4):
    if isinstance(x, list):
        return [short(v, nd) for v in x]
    return round(x, nd) if isinstance(x, float) else x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs-full", required=True)
    ap.add_argument("--stream", default="datasets/train_set/optmath-train-300-blind.jsonl")
    ap.add_argument("--vault", default="datasets/vault/optmath-train-300-labels.jsonl")
    ap.add_argument("--samples", default=DEFAULT)
    ap.add_argument("--out", default="outputs/additional_2026-11/divergence_packets")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    texts = {}
    for i, line in enumerate(open(a.stream, encoding="utf-8"), start=1):
        if line.strip():
            r = json.loads(line)
            sid = "sample_%s" % (r.get("index") if r.get("index") is not None else i)
            texts[sid] = r.get("question") or r.get("problem") or r.get("text") or json.dumps(r)[:4000]
    labels = {}
    for line in open(a.vault, encoding="utf-8"):
        if line.strip():
            r = json.loads(line); labels["sample_%s" % r["idx"]] = r["answer"]
    missing = []
    for sid in a.samples.split(","):
        d = os.path.join(a.runs_full, sid)
        vp = os.path.join(d, "verdict_full.json")
        if not os.path.isfile(vp):
            missing.append(sid); continue
        v = json.load(open(vp, encoding="utf-8"))
        L = ["# %s" % sid, "", "Decision: %s, clique %s, informative %s, label %s" %
             (v["decision"], v["clique"], v["informative"], labels.get(sid)), "", "## Problem text", "",
             texts.get(sid, "(not found in stream file)"), "", "## Values and statuses per instance", "",
             "| Candidate | " + " | ".join("inst %d" % k for k in range(len(v["instantiations"]))) + " |",
             "|---|" + "---|" * len(v["instantiations"])]
        for c in sorted(v["objectives"]):
            cells = ["%s (%s)" % (short(x), s[:24]) for x, s in zip(v["objectives"][c], v["statuses"][c])]
            L.append("| %s | %s |" % (c, " | ".join(cells)))
        L += ["", "## Sampled parameters per instance", ""]
        for k, inst in enumerate(v["instantiations"]):
            L.append("instance %d: `%s`" % (k, json.dumps(short(inst))[:3000]))
        sp = os.path.join(d, "spec.json")
        L += ["", "## Extracted specification", "", "```json",
              json.dumps(json.load(open(sp, encoding="utf-8")).get("spec"), indent=1)[:8000] if os.path.isfile(sp) else "(spec.json missing)",
              "```"]
        for c in sorted(v["objectives"]):
            cp = os.path.join(d, c + ".py")
            L += ["", "## Program %s" % c, "", "```python",
                  open(cp, encoding="utf-8").read() if os.path.isfile(cp) else "(program file missing)", "```"]
        open(os.path.join(a.out, sid + ".md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("written to %s; missing verdicts: %s" % (a.out, missing or "none"))


if __name__ == "__main__":
    main()
