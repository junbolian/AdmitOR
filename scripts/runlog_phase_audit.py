# -*- coding: utf-8 -*-
"""Phase and model-fidelity audit of the host run ledger (zero token).

Purpose
    Break the host LLM ledger down by phase and by requested-to-returned model
    pair, so the response-side model statement rests on counts.

Method
    The ledger records run_id "host" for every call, so phase is not stored.
    It is reconstructed from the host's runtime event streams: every
    outputs/**/runtime_logs/*.events.jsonl gives a [first ts, last ts] window
    for its run directory, and each ledger record is assigned to the window
    containing its timestamp. Records outside every window are reported as
    unattributed rather than guessed.

Inputs
    --runlog   host_llm.scrubbed.jsonl from the v1.0.0 release asset
               admitor-v1.0.0-runlogs.zip (release asset)
    --outputs  <host>/outputs, the tree holding runtime_logs
               (private, not distributed)
    --out      default reanalysis/reviewer_round

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

Reproduce (from the repository root)
    python scripts/runlog_phase_audit.py --runlog host_llm.scrubbed.jsonl --outputs <host>/outputs

Outputs
    <out>/01_3_runlog_phases.md and .csv

Paper location
    Appendix B pins paragraph (60,000 host calls: 58,575 deepseek-v3.2,
    1,425 deepseek-v3-2-251201; 5,025 unattributed).
"""
from __future__ import annotations

import argparse
import bisect
import collections
import csv
import datetime as dt
import glob
import json
import os
import sys

PINNED_HOST = {"deepseek-v3.2", "deepseek-v3-2-251201"}


def parse_ts(s):
    if not s:
        return None
    try:
        return dt.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        try:
            return dt.datetime.fromisoformat(s)
        except ValueError:
            return None


def phase_label(run_dir, outputs_root):
    rel = os.path.relpath(run_dir, outputs_root).replace(os.sep, "/")
    parts = rel.split("/")
    if parts[0] == "eval":
        return "E0 eval / " + (parts[1] if len(parts) > 1 else "?")
    if parts[0] == "e1":
        if len(parts) > 1 and parts[1].startswith("collect"):
            return "E1 " + parts[1]
        if len(parts) > 3 and parts[1] == "eval":
            return "E1 eval / %s / %s" % (parts[2], parts[3])
        if len(parts) > 2 and parts[1] == "eval":
            return "E1 eval / %s" % parts[2]
        return "E1 " + "/".join(parts[1:])
    if parts[0] == "e3":
        return "E3 " + "/".join(parts[1:]) if len(parts) > 1 else "E3"
    return rel


def windows(outputs_root):
    """[(start, end, label, run_dir)] from every runtime event stream."""
    out = []
    pat = os.path.join(outputs_root, "**", "runtime_logs", "*.events.jsonl")
    for f in glob.glob(pat, recursive=True):
        run_dir = os.path.dirname(os.path.dirname(f))
        lo = hi = None
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        t = parse_ts(json.loads(line).get("ts"))
                    except Exception:
                        continue
                    if t is None:
                        continue
                    lo = t if lo is None or t < lo else lo
                    hi = t if hi is None or t > hi else hi
        except OSError:
            continue
        if lo and hi:
            out.append((lo, hi, phase_label(run_dir, outputs_root), run_dir))
    out.sort(key=lambda r: r[0])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--runlog", required=True)
    ap.add_argument("--outputs", required=True)
    ap.add_argument("--out", default="reanalysis/reviewer_round")
    a = ap.parse_args()

    wins = windows(a.outputs)
    starts = [w[0] for w in wins]
    print("runtime event streams found: %d" % len(wins))

    per_phase = collections.defaultdict(collections.Counter)   # phase -> (req,resp)
    kinds = collections.Counter()
    fam_strat = collections.Counter()
    unattributed = collections.Counter()
    n_llm = 0
    span_lo = span_hi = None

    with open(a.runlog, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                kinds["<unparseable>"] += 1
                continue
            kinds[r.get("kind")] += 1
            if r.get("kind") != "llm":
                continue
            n_llm += 1
            fam_strat[(r.get("family"), r.get("strategy"))] += 1
            t = parse_ts(r.get("ts"))
            if t:
                span_lo = t if span_lo is None or t < span_lo else span_lo
                span_hi = t if span_hi is None or t > span_hi else span_hi
            req = r.get("model")
            resp = None
            for tag in (r.get("tags") or []):
                if isinstance(tag, str) and tag.startswith("resp_model:"):
                    resp = tag.split(":", 1)[1]
            label = None
            if t is not None:
                i = bisect.bisect_right(starts, t) - 1
                # scan back a little: windows can nest or overlap
                for j in range(max(0, i - 6), min(len(wins), i + 2)):
                    lo, hi, lab, _d = wins[j]
                    if lo <= t <= hi:
                        label = lab
                        break
            if label is None:
                label = "(unattributed)"
                unattributed[t.date().isoformat() if t else "?"] += 1
            per_phase[label][(req, resp)] += 1

    os.makedirs(a.out, exist_ok=True)
    md = os.path.join(a.out, "01_3_runlog_phases.md")
    cv = os.path.join(a.out, "01_3_runlog_phases.csv")

    L = []
    def w(s=""):
        L.append(s)

    w("# Task 1.3 extension. Host ledger by phase and model pair")
    w()
    w("Zero-token. Generated by `admitor-infra/runlog_phase_audit.py`.")
    w()
    w("```powershell")
    w("conda activate admitor")
    w("python admitor-infra\\runlog_phase_audit.py `")
    w("    --runlog OptSkills-main\\runs\\host_llm.jsonl `")
    w("    --outputs OptSkills-main\\outputs `")
    w("    --out AdmitOR\\reanalysis\\reviewer_round")
    w("```")
    w()
    w("## Ledger totals")
    w()
    w("| Field | Value |")
    w("|---|---|")
    for k, v in kinds.most_common():
        w("| records of kind `%s` | %d |" % (k, v))
    w("| llm timestamp span | %s to %s |" % (span_lo, span_hi))
    w("| runtime event streams used for windows | %d |" % len(wins))
    w()
    w("Every `llm` record carries `(family, strategy)`:")
    w()
    for k, v in fam_strat.most_common():
        w("- `%s` -> %d" % (k, v))
    w()
    w("## Per-phase requested to returned model")
    w()
    w("| Phase | requested | returned | count |")
    w("|---|---|---|---:|")
    rows = []
    for phase in sorted(per_phase):
        for (req, resp), n in sorted(per_phase[phase].items(), key=lambda x: -x[1]):
            flag = "" if resp in PINNED_HOST else "  **OUTSIDE PIN**"
            w("| %s | `%s` | `%s`%s | %d |" % (phase, req, resp, flag, n))
            rows.append({"phase": phase, "requested": req, "returned": resp, "count": n})
    w()
    w("## deepseek-v3-2-251201 responses per phase")
    w()
    w("| Phase | count | share of phase |")
    w("|---|---:|---:|")
    tot_dated = 0
    for phase in sorted(per_phase):
        tot = sum(per_phase[phase].values())
        d = sum(n for (rq, rs), n in per_phase[phase].items() if rs == "deepseek-v3-2-251201")
        tot_dated += d
        if d:
            w("| %s | %d | %.1f%% |" % (phase, d, 100.0 * d / tot))
    w("| **total** | **%d** | |" % tot_dated)
    w()
    w("## Responses outside the pinned set")
    w()
    outside = collections.Counter()
    for phase in per_phase:
        for (rq, rs), n in per_phase[phase].items():
            if rs not in PINNED_HOST:
                outside[(phase, rq, rs)] += n
    if outside:
        w("| Phase | requested | returned | count |")
        w("|---|---|---|---:|")
        for (p, rq, rs), n in outside.most_common():
            w("| %s | `%s` | `%s` | %d |" % (p, rq, rs, n))
    else:
        w("None. Every `llm` record returned a string inside "
          "{deepseek-v3.2, deepseek-v3-2-251201}.")
    w()
    if unattributed:
        w("## Unattributed records (no runtime window contains the timestamp)")
        w()
        w("| Date | count |")
        w("|---|---:|")
        for d, n in sorted(unattributed.items()):
            w("| %s | %d |" % (d, n))
        w()
    w("## Extraction and candidate-arm calls")
    w()
    w("Not present in this ledger. All %d `llm` records carry "
      "`family=deepseek, strategy=host`, which is the host transport only. "
      "The gate's extraction and the three candidate arms call the endpoint "
      "through AdmitOR's own client in `admitor/pipeline_one.py`, which is not "
      "wrapped by `runlog.py`, so no response-side model string was recorded "
      "for them. Their call volume is recoverable from the stored artifacts "
      "(spec.json and the per-candidate .py files), their response models are "
      "not." % n_llm)
    w()

    open(md, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    with open(cv, "w", encoding="utf-8", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=["phase", "requested", "returned", "count"])
        wtr.writeheader()
        wtr.writerows(rows)
    print("wrote %s" % md)
    print("wrote %s" % cv)
    print()
    print("llm records: %d   phases: %d   dated-variant responses: %d"
          % (n_llm, len(per_phase), tot_dated))
    print("responses outside pin: %d" % sum(outside.values()))
    print("unattributed: %d" % sum(unattributed.values()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
