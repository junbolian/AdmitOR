# -*- coding: utf-8 -*-
"""Serving-variant by eval-outcome join (zero token).

Purpose
    1,425 of the 60,000 host calls returned `deepseek-v3-2-251201` rather than
    `deepseek-v3.2`, concentrated in the ground-truth arm. This decides from
    data whether selection failures or accuracy track the serving variant.

Attribution method, in the order tried, with the method recorded per item
    1. cache join. The eval response cache stores one response document per
       call, each carrying its own `model` field. A call is attributed to an
       eval item by matching the response payload the item recorded
       (assistant message content, or the serialized tool_calls when content
       is null) against the same field in the cache document.
    2. runlog join. Not usable: the ledger stores only a 16-hex digest of the
       request and no request body survives, so the digest cannot be
       recomputed. Recorded as unavailable.
    3. time-window fallback. Items with no cache match are left
       `unattributed`, because the eval ran with 12 concurrent workers and a
       window cannot separate concurrent calls. The count is reported.

Inputs
    --eval-root  <host>/outputs/e1/eval (private, not distributed)
    --cache      <host>/outputs/e1/llm_cache_eval, the response cache
                 (private, not distributed)
    --out        default reanalysis/reviewer_round

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

This script is not runnable from the public checkout alone.

Reproduce (from the repository root)
    python scripts/serving_variant_join.py --eval-root <host>/outputs/e1/eval --cache <host>/outputs/e1/llm_cache_eval

Outputs
    <out>/05b_serving_variant_join.md and .csv

Paper location
    Appendix B pins paragraph.
"""
from __future__ import annotations

import argparse
import collections
import csv
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_eval import round_aware, to_num  # noqa: E402

ARMS = ["gt", "vote", "runsok", "gate"]
PLATES = ["optibench", "mamo_c", "complexor", "industryor", "optmath"]
PINNED = "deepseek-v3.2"
VARIANT = "deepseek-v3-2-251201"

try:
    from scipy.stats import fisher_exact
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


def h(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def payload_keys(msg):
    """Hashable fingerprints of one assistant response payload."""
    out = []
    c = msg.get("content")
    if isinstance(c, str) and c.strip():
        out.append(h(c))
    tc = msg.get("tool_calls")
    if tc:
        try:
            out.append(h(json.dumps(tc, sort_keys=True, ensure_ascii=False)))
        except Exception:
            pass
        for call in tc:
            fn = (call or {}).get("function") or {}
            args = fn.get("arguments")
            if isinstance(args, str) and args.strip():
                out.append(h(args))
    return out


def build_cache_index(cache_dir):
    idx = {}
    n = 0
    for f in glob.glob(os.path.join(cache_dir, "*.json")):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:
            continue
        n += 1
        model = d.get("model")
        try:
            msg = d["choices"][0]["message"]
        except Exception:
            continue
        for k in payload_keys(msg):
            idx.setdefault(k, model)
    return idx, n


def main():
    ap = argparse.ArgumentParser(description="Task 5b serving-variant join.")
    ap.add_argument("--eval-root", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", default="reanalysis/reviewer_round")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    idx, n_cache = build_cache_index(a.cache)
    print("cache documents indexed: %d, fingerprints: %d" % (n_cache, len(idx)))

    rows = []
    per = collections.defaultdict(lambda: collections.Counter())
    gt_opti_selector = collections.Counter()

    for arm in ARMS:
        for plate in PLATES:
            p = os.path.join(a.eval_root, arm, plate, "trajectories.jsonl")
            if not os.path.isfile(p):
                continue
            for line in open(p, encoding="utf-8"):
                if not line.strip():
                    continue
                r = json.loads(line)
                sid = str(r.get("sample_id"))
                failed = bool(r.get("e1_eval_failure"))
                ok = round_aware(to_num(r.get("prediction")),
                                 to_num(r.get("answer")), r.get("answer"))
                models = []
                fa = r.get("function_agent") or {}
                for m in (fa.get("messages") or []):
                    if m.get("role") != "assistant":
                        continue
                    for k in payload_keys(m):
                        if k in idx:
                            models.append(idx[k])
                            break
                ss = r.get("skill_selection") or {}
                raw = ss.get("raw") if isinstance(ss, dict) else None
                sel_model = None
                if isinstance(raw, str) and raw.strip():
                    sel_model = idx.get(h(raw))
                    if sel_model:
                        models.append(sel_model)
                if not models:
                    cls = "unattributed"
                elif any(m == VARIANT for m in models):
                    cls = "any_variant"
                else:
                    cls = "all_pinned"
                per[(arm, plate)][cls] += 1
                per[(arm, plate)][("fail", cls)] += 1 if failed else 0
                per[(arm, plate)][("ok", cls)] += 1 if ok else 0
                rows.append(dict(arm=arm, plate=plate, sample_id=sid, cls=cls,
                                 n_calls_attributed=len(models),
                                 e1_eval_failure=int(failed),
                                 round_aware_correct=int(ok),
                                 method="cache" if models else "none"))
                if arm == "gt" and plate == "optibench" and failed:
                    gt_opti_selector[sel_model or "unattributed"] += 1

    L = []

    def w(s=""):
        L.append(s)

    w("# Task 5b. Serving variant by eval outcome")
    w()
    w("Zero-token. Generated by `admitor-infra/serving_variant_join.py`.")
    w()
    w("## Attribution method")
    w()
    w("| Method | Status |")
    w("|---|---|")
    w("| 1 cache join (response payload -> cache `model`) | used; %d documents "
      "indexed, %d distinct payload fingerprints |" % (n_cache, len(idx)))
    w("| 2 runlog join (recompute `prompt_hash`) | **unavailable**: `runlog.py` "
      "stores only a 16-hex digest of a sorted-keys dump and no request body "
      "survives, so the digest cannot be recomputed |")
    w("| 3 time-window fallback | **not used**: the eval ran 12 concurrent "
      "workers, so a window cannot separate concurrent calls; such items are "
      "left `unattributed` |")
    w()
    w("Cache `model` field over all documents: "
      "`deepseek-v3.2` and `deepseek-v3-2-251201` only.")
    w()
    w("## Per arm and plate")
    w()
    w("| Arm | Plate | items | all_pinned | any_variant | unattributed | "
      "fail rate pinned | fail rate variant | acc pinned | acc variant |")
    w("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    order = [("gt", "optibench"), ("gt", "mamo_c")]
    order += [(x, y) for x in ARMS for y in PLATES if (x, y) not in order]
    for key in order:
        c = per.get(key)
        if not c:
            continue
        arm, plate = key
        n = sum(c[k] for k in ("all_pinned", "any_variant", "unattributed"))

        def rate(num, den):
            return "%.1f%%" % (100.0 * num / den) if den else "-"
        ap_, av = c["all_pinned"], c["any_variant"]
        w("| %s | %s | %d | %d | %d | %d | %s | %s | %s | %s |"
          % (arm, plate, n, ap_, av, c["unattributed"],
             rate(c[("fail", "all_pinned")], ap_),
             rate(c[("fail", "any_variant")], av),
             rate(c[("ok", "all_pinned")], ap_),
             rate(c[("ok", "any_variant")], av)))
    w()
    w("## Fisher exact, two-sided, all_pinned against any_variant")
    w()
    w("| Arm | Plate | table (pinned fail, pinned ok / variant fail, variant ok) | "
      "p failure | p accuracy |")
    w("|---|---|---|---|---|")
    for key in order:
        c = per.get(key)
        if not c:
            continue
        arm, plate = key
        ap_, av = c["all_pinned"], c["any_variant"]
        if ap_ == 0 or av == 0:
            continue
        fp, fv = c[("fail", "all_pinned")], c[("fail", "any_variant")]
        op, ov = c[("ok", "all_pinned")], c[("ok", "any_variant")]
        if HAVE_SCIPY:
            p1 = fisher_exact([[fp, ap_ - fp], [fv, av - fv]])[1]
            p2 = fisher_exact([[op, ap_ - op], [ov, av - ov]])[1]
            s1, s2 = "%.4f" % p1, "%.4f" % p2
        else:
            s1 = s2 = "scipy absent"
        w("| %s | %s | %d,%d / %d,%d | %s | %s |"
          % (arm, plate, fp, ap_ - fp, fv, av - fv, s1, s2))
    w()
    w("## The 85 failing gt/OptiBench items, selector call serving name")
    w()
    w("| Selector call served as | count |")
    w("|---|---:|")
    for k, v in gt_opti_selector.most_common():
        w("| `%s` | %d |" % (k, v))
    w("| **total** | **%d** |" % sum(gt_opti_selector.values()))
    w()

    md = os.path.join(a.out, "05b_serving_variant_join.md")
    open(md, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    cv = os.path.join(a.out, "05b_serving_variant_join.csv")
    with open(cv, "w", encoding="utf-8", newline="") as fh:
        wtr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wtr.writeheader()
        wtr.writerows(rows)
    print("wrote", md)
    print("wrote", cv)
    tot = collections.Counter(r["cls"] for r in rows)
    print("overall class counts:", dict(tot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
