# -*- coding: utf-8 -*-
"""Code-fact counts for the reviewer round (zero token, read-only).

Purpose
    Count, from stored artifacts, the facts the manuscript states about the
    consensus step: the informative-instance rule and tolerance as exercised,
    specifications with integer parameters, relative versus absolute
    perturbation modes, infeasible resampled instances, problems with no
    solvable instance, and the samples that ended in ERROR.

Inputs
    --stream-runs  <host>/outputs/e1/certify_runs; needs spec.json next to each
                   verdict_full.json (private, not distributed; the
                   verdict_full.json files alone are in git under
                   artifacts/e1/certify_runs)
    --calib-runs   <host>/outputs/e3/certify_runs (private, not distributed)
    --collect      <host>/outputs/e1/collect/trajectories.jsonl
                   (private, not distributed)
    --libs         artifacts/e1/libraries (in git)
    --out          default reanalysis/reviewer_round

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

Reproduce (from the repository root)
    python scripts/code_facts.py --stream-runs <host>/outputs/e1/certify_runs --calib-runs <host>/outputs/e3/certify_runs --collect <host>/outputs/e1/collect/trajectories.jsonl

Outputs
    <out>/01_code_facts_data.md

Paper location
    Section 3 Step 2 and Step 3 (informative rule, tolerance); Appendix A
    remark (5) (173 of 298 specifications with integer parameters).
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import statistics
import sys


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def flatten(x):
    if isinstance(x, (list, tuple)):
        for v in x:
            yield from flatten(v)
    else:
        yield x


def spec_params(spec_path):
    """Return the {name: entry} parameter dict from a stored spec.json."""
    d = load(spec_path)
    s = d.get("spec")
    return s if isinstance(s, dict) else {}


def integer_audit(runs_dir):
    n_spec = n_with_int = 0
    n_int_params = n_rel = n_abs = n_other = 0
    for sp in sorted(glob.glob(os.path.join(runs_dir, "*", "spec.json"))):
        try:
            params = spec_params(sp)
        except Exception:
            continue
        n_spec += 1
        has_int = False
        for _name, e in params.items():
            p = e.get("perturb") if isinstance(e, dict) else None
            if not isinstance(p, dict):
                n_other += 1
                continue
            mode = str(p.get("mode", "")).lower()
            if mode == "rel":
                n_rel += 1
            elif mode == "abs":
                n_abs += 1
            else:
                n_other += 1
            if p.get("integer") is True:
                n_int_params += 1
                has_int = True
        n_with_int += 1 if has_int else 0
    return dict(specs=n_spec, specs_with_integer=n_with_int,
                integer_params=n_int_params, rel=n_rel, abs=n_abs, other=n_other)


def status_audit(runs_dir):
    """Infeasible share over (candidate, resampled instance) pairs."""
    pairs = infeas = 0
    all_infeasible_problems = 0
    decisions = collections.Counter()
    status_kinds = collections.Counter()
    n_runs = 0
    for d in sorted(os.listdir(runs_dir)):
        vf = os.path.join(runs_dir, d, "verdict_full.json")
        if not os.path.isfile(vf):
            continue
        n_runs += 1
        v = load(vf)
        decisions[v.get("decision")] += 1
        sta = v.get("statuses") or {}
        objs = v.get("objectives") or {}
        # candidates that solved the base instance (index 0)
        base_ok = [c for c in objs
                   if isinstance(objs[c], list) and objs[c] and objs[c][0] is not None]
        any_ok_resample = False
        for c, series in sta.items():
            if not isinstance(series, list):
                continue
            for k, s in enumerate(series):
                if k == 0:          # index 0 is the stated instance
                    continue
                pairs += 1
                low = str(s).lower()
                if "infeas" in low or "unbounded" in low:
                    infeas += 1
                    status_kinds["infeasible_or_unbounded"] += 1
                elif "optimal" in low:
                    status_kinds["optimal"] += 1
                    if c in base_ok:
                        any_ok_resample = True
                elif "crash" in low or "error" in low or "exception" in low:
                    status_kinds["crash"] += 1
                elif "timeout" in low:
                    status_kinds["timeout"] += 1
                else:
                    status_kinds["other:" + low[:20]] += 1
        if base_ok and not any_ok_resample:
            all_infeasible_problems += 1
    return dict(runs=n_runs, pairs=pairs, infeasible=infeas,
                all_resamples_dead=all_infeasible_problems,
                decisions=decisions, status_kinds=status_kinds)


def main():
    ap = argparse.ArgumentParser(description="Task 1 data-driven facts.")
    ap.add_argument("--stream-runs", required=True)
    ap.add_argument("--calib-runs", required=True)
    ap.add_argument("--collect", required=True)
    ap.add_argument("--libs", default="artifacts/e1/libraries")
    ap.add_argument("--out", default="reanalysis/reviewer_round")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    L = []

    def w(s=""):
        L.append(s)

    w("# Task 1. Code facts, data-driven parts")
    w()
    w("Zero-token. Generated by `admitor-infra/code_facts.py`.")
    w()

    # ---- 1.4 -------------------------------------------------------------
    w("## 1.4 Integer-flagged parameters")
    w()
    st = integer_audit(a.stream_runs)
    cal = integer_audit(a.calib_runs)
    w("| Set | specs | specs with >=1 integer param | integer params | rel | abs | other |")
    w("|---|---:|---:|---:|---:|---:|---:|")
    for nm, d in (("stream (300)", st), ("calibration (150)", cal)):
        w("| %s | %d | %d | %d | %d | %d | %d |"
          % (nm, d["specs"], d["specs_with_integer"], d["integer_params"],
             d["rel"], d["abs"], d["other"]))
    w()
    w("Sampler treatment of an integer-flagged parameter, "
      "`admitor-core/consensus.py`:")
    w()
    w("```python")
    w("# _perturb_rel (line 78) and _fill_abs (line 87)")
    w("v = base * rng.uniform(1 - r, 1 + r)      # rel")
    w("v = rng.uniform(lo, hi)                    # abs")
    w("return round(v) if integer else v          # both")
    w("```")
    w()
    w("Fact: the draw is continuous and then rounded to the nearest integer. "
      "It is not an integer-uniform draw, and `rel` mode honours the flag only "
      "through the same rounding.")
    w()

    # ---- 1.5 -------------------------------------------------------------
    w("## 1.5 Infeasible resampled instances")
    w()
    s = status_audit(a.stream_runs)
    w("| Quantity | Value |")
    w("|---|---:|")
    w("| runs read | %d |" % s["runs"])
    w("| (candidate, resampled instance) pairs | %d |" % s["pairs"])
    w("| pairs with infeasible or unbounded status | %d |" % s["infeasible"])
    w("| share | %.1f%% |" % (100.0 * s["infeasible"] / max(s["pairs"], 1)))
    w("| problems where every resampled instance failed for every base-solving candidate | %d |"
      % s["all_resamples_dead"])
    w()
    w("Status kinds over resampled instances:")
    w()
    for k, v in s["status_kinds"].most_common(8):
        w("- `%s` -> %d" % (k, v))
    w()

    # ---- 1.10 ------------------------------------------------------------
    w("## 1.10 Certification bookkeeping")
    w()
    w("| decision | count |")
    w("|---|---:|")
    for k, v in s["decisions"].most_common():
        w("| `%s` | %d |" % (k, v))
    w("| **total verdict_full.json** | **%d** |" % s["runs"])
    w()

    # ---- 1.6 -------------------------------------------------------------
    w("## 1.6 Vote judge: which candidate set")
    w()
    w("`admitor-core/label_oracle.py:135` reads the host's own rollout:")
    w()
    w("```python")
    w("def row_candidates(row):")
    w("    rollout = row.get('rollout', {})")
    w("    cands = rollout.get('candidates', []) if isinstance(rollout, dict) else []")
    w("    return [c for c in cands if isinstance(c, dict)]")
    w("```")
    w()
    per = []
    succ = []
    try:
        with open(a.collect, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                r = json.loads(line)
                cs = (r.get("rollout") or {}).get("candidates") or []
                per.append(len(cs))
                ok = sum(1 for c in cs
                         if isinstance(c, dict)
                         and (c.get("run_result") or {}).get("returncode") == 0
                         and (c.get("run_result") or {}).get("result") is not None)
                succ.append(ok)
    except OSError as e:
        w("Collect trajectories unreadable: %s" % e)
    if per:
        w("| Host trajectories per problem | min | median | max | mean |")
        w("|---|---:|---:|---:|---:|")
        w("| all candidates | %d | %.0f | %d | %.2f |"
          % (min(per), statistics.median(per), max(per), sum(per) / len(per)))
        w("| successful candidates | %d | %.0f | %d | %.2f |"
          % (min(succ), statistics.median(succ), max(succ), sum(succ) / len(succ)))
        w()
        w("Problems read: %d" % len(per))
        w()
    w("Tie resolution, `label_oracle.py:218`: a unique modal 2dp value with "
      "count >= 2 is required; an all-distinct set, an all-failed set, or a tie "
      "between two modes all return the `NO_CONSENSUS` sentinel.")
    w()

    # ---- 1.7 -------------------------------------------------------------
    w("## 1.7 Admitted candidates to library files")
    w()
    w("`build_summary.clusters` is a list of cluster records, each with "
      "`sample_count`, `candidate_count`, `built` and `record.path`.")
    w()
    w("| Arm | input_count | eligible | ineligible | clusters | built | not built | files on disk |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    gate_cl = None
    for arm in ("gt", "vote", "runsok", "gate"):
        bs = os.path.join(a.libs, "skill_library_%s.build_summary.json" % arm)
        d = os.path.join(a.libs, "skill_library_%s" % arm)
        files = len(os.listdir(d)) if os.path.isdir(d) else None
        if not os.path.isfile(bs):
            w("| %s | - | - | - | - | - | - | %s |" % (arm, files))
            continue
        b = load(bs)
        sm = b.get("build_summary") or {}
        cl = sm.get("clusters")
        cl = cl if isinstance(cl, list) else []
        built = sum(1 for c in cl if c.get("built"))
        if arm == "gate":
            gate_cl = cl
        w("| %s | %s | %s | %s | %d | %d | %d | %s |"
          % (arm, sm.get("input_count"), sm.get("eligible_count"),
             sm.get("ineligible_count"), len(cl), built, len(cl) - built, files))
    if gate_cl:
        cand = [c.get("candidate_count") or 0 for c in gate_cl]
        samp = [c.get("sample_count") or 0 for c in gate_cl]
        bcand = [c.get("candidate_count") or 0 for c in gate_cl if c.get("built")]
        w()
        w("Gate arm cluster geometry:")
        w()
        w("| Quantity | Value |")
        w("|---|---:|")
        w("| clusters | %d |" % len(gate_cl))
        w("| clusters built into a file | %d |" % sum(1 for c in gate_cl if c.get("built")))
        w("| admitted candidates summed over clusters | %d |" % sum(cand))
        w("| candidates in built clusters | %d |" % sum(bcand))
        w("| samples summed over clusters | %d |" % sum(samp))
        w("| candidates per cluster: min / median / max | %d / %d / %d |"
          % (min(cand), int(statistics.median(cand)), max(cand)))
        w("| distinct file paths in records | %d |"
          % len({(c.get("record") or {}).get("path") for c in gate_cl
                 if (c.get("record") or {}).get("path")}))
        w()
        w("Candidates-per-cluster histogram (count: n_clusters): `%s`"
          % dict(sorted(collections.Counter(cand).items())))
    w()

    p = os.path.join(a.out, "01_code_facts_data.md")
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("wrote", p)
    print()
    print("1.4 stream:", st)
    print("1.4 calib :", cal)
    print("1.5 pairs=%d infeasible=%d (%.1f%%) all-dead-problems=%d"
          % (s["pairs"], s["infeasible"],
             100.0 * s["infeasible"] / max(s["pairs"], 1), s["all_resamples_dead"]))
    print("1.10 decisions:", dict(s["decisions"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
