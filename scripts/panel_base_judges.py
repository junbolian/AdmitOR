# -*- coding: utf-8 -*-
"""Judge ablation on the stored records: problem-level decomposition (zero token).

Purpose
    Separate the two factors the gate's gain confounds: unanimity of the
    panel at the stated instance, and agreement across resampled instances.
    Every judge is computed from stored `objectives[cand][0]` values and
    stored verdicts; no model is called.

Judges
    panel_base_2of3    >=2 candidates with finite base values that agree.
                       Certificate = base value of the first candidate in id
                       order (A, B, C) of the largest agreeing set. When the
                       agreement relation is a chain (A~B, B~C, not A~C) no
                       certificate is emitted and the case is counted.
    panel_base_3of3    all three base values finite and pairwise agreeing.
    gate_asdeployed    decision ACCEPT and value not None; the rule that built
                       the E1 library.
    gate_tau           gate_asdeployed and deployed score >= 33.3.
    host_vote          the released Vote oracle over the host's own three
                       trajectories (modal 2dp value, count >= 2, unique).

Agreement rule, as in admitor/consensus.py
    abs(a - b) <= tol_rel * max(1.0, abs(a), abs(b)),  tol_rel = 1e-4

Inputs
    --runs     artifacts/e1/certify_runs (in git)
    --collect  <host>/outputs/e1/collect/trajectories.jsonl, for host_vote
               (private, not distributed)
    --vault    datasets/vault/optmath-train-300-labels.jsonl (in git)
    --out      default reanalysis/reviewer_round

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

Reproduce (from the repository root)
    python scripts/panel_base_judges.py --collect <host>/outputs/e1/collect/trajectories.jsonl

Outputs
    <out>/03_verdicts/<judge>/<sample_id>.json (GateOracle-shaped),
    <out>/03_decomposition_problem.csv, 03_pairs.csv, 03_decomposition.md

Paper location
    Section 4.2 Table 3 and Appendix C "Judge ablation details".
"""
from __future__ import annotations

import argparse
import collections
import csv
import itertools
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))  # repository root, for admitor/
from label_oracle import VoteOracle, row_candidates  # noqa: E402
from score_eval import round_aware, to_num  # noqa: E402

TOL_REL = 1e-4                      # consensus.py run_l3 default
DEV = {"sample_%d" % i for i in (1, 2, 3, 4, 5)}
ORDER = ["A-direct", "B-structured", "C-direct"]
JUDGES = ["panel_base_2of3", "panel_base_3of3", "gate_asdeployed",
          "gate_tau", "host_vote"]

try:
    from scipy.stats import beta as _beta
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


def cp_upper(k, n, delta):
    if n == 0:
        return float("nan")
    if k >= n:
        return 1.0
    if HAVE_SCIPY:
        return float(_beta.ppf(1.0 - delta, k + 1, n - k))
    import math
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        cdf = sum(math.comb(n, i) * mid ** i * (1 - mid) ** (n - i)
                  for i in range(0, k + 1))
        lo, hi = (mid, hi) if cdf > delta else (lo, mid)
    return hi


def close(a, b):
    return abs(a - b) <= TOL_REL * max(1.0, abs(a), abs(b))


def verdict_score(v):
    clique = v.get("clique") or []
    fams = {str(m)[:1] for m in clique}
    return 10.0 * len(fams) + len(clique) + len(v.get("informative") or []) / 10.0


def base_values(v):
    obj = v.get("objectives") or {}
    out = {}
    for c in ORDER:
        s = obj.get(c)
        if isinstance(s, list) and s and s[0] is not None:
            try:
                out[c] = float(s[0])
            except (TypeError, ValueError):
                pass
    return out


def panel_judgements(bv):
    """Return (cert_2of3, cert_3of3, is_chain)."""
    ids = [c for c in ORDER if c in bv]
    pairs = [(x, y) for x, y in itertools.combinations(ids, 2)
             if close(bv[x], bv[y])]
    triple = len(ids) == 3 and len(pairs) == 3
    c3 = bv[ORDER[0]] if triple else None
    if triple:
        return bv[ids[0]], c3, False
    if len(pairs) == 1:
        x, y = pairs[0]
        first = x if ORDER.index(x) < ORDER.index(y) else y
        return bv[first], c3, False
    if len(pairs) >= 2:
        return None, c3, True          # chain: two agreeing pairs, no triple
    return None, c3, False


def main():
    ap = argparse.ArgumentParser(description="Task 3 decomposition.")
    ap.add_argument("--runs", default="artifacts/e1/certify_runs")
    ap.add_argument("--collect", required=True)
    ap.add_argument("--vault", default="datasets/vault/optmath-train-300-labels.jsonl")
    ap.add_argument("--out", default="reanalysis/reviewer_round")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)

    vault = {}
    for line in open(a.vault, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            vault["sample_%s" % r["idx"]] = str(r.get("answer"))

    # host_vote from the collect trajectories
    vo = VoteOracle()
    hv = {}
    for line in open(a.collect, encoding="utf-8"):
        if not line.strip():
            continue
        row = json.loads(line)
        sid = str(row.get("sample_id"))
        g = vo.effective_gt(row)
        hv[sid] = None if (g is None or str(g) == "1e308") else str(g)

    per = {}
    chain_cases = []
    for d in sorted(os.listdir(a.runs)):
        p = os.path.join(a.runs, d, "verdict_full.json")
        if not os.path.isfile(p):
            continue
        v = json.load(open(p, encoding="utf-8"))
        bv = base_values(v)
        c2, c3, chain = panel_judgements(bv)
        if chain:
            chain_cases.append(d)
        dec = str(v.get("decision", "")).upper()
        clique = v.get("clique") or []
        gv = None
        if dec == "ACCEPT" and clique:
            s = (v.get("objectives") or {}).get(clique[0]) or []
            gv = s[0] if s else None
        sc = verdict_score(v)
        per[d] = dict(
            sample_id=d, decision=dec, score=sc,
            n_fam=len({str(m)[:1] for m in clique}),
            n_informative=len(v.get("informative") or []),
            panel_base_2of3=c2, panel_base_3of3=c3,
            gate_asdeployed=gv,
            gate_tau=(gv if (gv is not None and sc >= 33.3) else None),
            host_vote=hv.get(d), chain=chain,
        )

    # ---- 3.1 derived verdicts -------------------------------------------
    vroot = os.path.join(a.out, "03_verdicts")
    for j in JUDGES:
        os.makedirs(os.path.join(vroot, j), exist_ok=True)
    for sid, r in per.items():
        for j in JUDGES:
            val = r[j]
            doc = {"sample_id": sid,
                   "decision": "ACCEPT" if val is not None else "ABSTAIN",
                   "clique_value": (float(val) if val is not None
                                    and str(val).replace(".", "", 1)
                                    .replace("-", "", 1).isdigit() else val)}
            with open(os.path.join(vroot, j, sid + ".json"), "w",
                      encoding="utf-8", newline="\n") as fh:
                json.dump(doc, fh, ensure_ascii=False)

    # ---- 3.2 problem-level accuracy --------------------------------------
    nd = [r for s, r in per.items() if s not in DEV]
    L, prows = [], []

    def w(s=""):
        L.append(s)

    w("# Task 3. Consensus versus perturbation decomposition")
    w()
    w("Zero-token. Generated by `admitor-infra/panel_base_judges.py`.")
    w("Agreement rule verbatim from `consensus.py:125`: "
      "`abs(a-b) <= 1e-4 * max(1.0, |a|, |b|)`.")
    w()
    w("## 3.2 Problem-level certificate accuracy (round-aware, non-dev)")
    w()
    w("| Judge | n certified | n wrong | false proportion | CP95 upper | CP98.75 upper |")
    w("|---|---:|---:|---:|---:|---:|")
    for j in JUDGES:
        cert = [r for r in nd if r[j] is not None and vault.get(r["sample_id"])]
        wrong = [r for r in cert
                 if not round_aware(to_num(r[j]), to_num(vault[r["sample_id"]]),
                                    vault[r["sample_id"]])]
        n, k = len(cert), len(wrong)
        w("| `%s` | %d | %d | %s | %s | %s |"
          % (j, n, k, "%.4f" % (k / n) if n else "-",
             "%.4f" % cp_upper(k, n, 0.05) if n else "-",
             "%.4f" % cp_upper(k, n, 0.0125) if n else "-"))
        prows.append(dict(judge=j, n_certified=n, n_wrong=k,
                          false_proportion=round(k / n, 6) if n else "",
                          cp95=round(cp_upper(k, n, 0.05), 6) if n else "",
                          cp9875=round(cp_upper(k, n, 0.0125), 6) if n else ""))
    w()
    w("`runsok` defines no problem-level certificate: its rule is per-candidate "
      "execution success, which yields no certified value to grade.")
    w()
    w("Chain cases (two agreeing pairs, no triple, no certificate emitted): "
      "**%d**%s" % (len(chain_cases),
                    (" -> `%s`" % ", ".join(chain_cases)) if chain_cases else ""))
    w()

    # ---- 3.4 pair counts --------------------------------------------------
    def rw(r, j):
        """round-aware correctness of judge j's certificate."""
        ans = vault.get(r["sample_id"])
        if r[j] is None or ans is None:
            return None
        return round_aware(to_num(r[j]), to_num(ans), ans)

    pair_rows = []
    w("## 3.4 Pair A, at-least-two-families level")
    w()
    w("Problems with a `panel_base_2of3` certificate, split by the gate's "
      "decision, with the vault correctness of the base-agreed certificate.")
    w()
    w("| Gate outcome | problems | base-agreed cert wrong | right |")
    w("|---|---:|---:|---:|")
    p2 = [r for r in nd if r["panel_base_2of3"] is not None]
    buckets = collections.defaultdict(list)
    for r in p2:
        if r["decision"] == "ACCEPT" and r["gate_asdeployed"] is not None:
            buckets["ACCEPT value-bearing"].append(r)
        elif r["decision"] == "ACCEPT":
            buckets["ACCEPT without base value"].append(r)
        else:
            buckets[r["decision"] or "ERROR"].append(r)
    for k in sorted(buckets):
        rs = buckets[k]
        bad = sum(1 for r in rs if rw(r, "panel_base_2of3") is False)
        good = sum(1 for r in rs if rw(r, "panel_base_2of3") is True)
        w("| %s | %d | %d | %d |" % (k, len(rs), bad, good))
        pair_rows.append(dict(pair="A", bucket=k, n=len(rs), wrong=bad, right=good))
    w("| **total** | **%d** | | |" % len(p2))
    w()
    only_gate = [r for r in nd
                 if r["gate_asdeployed"] is not None and r["panel_base_2of3"] is None]
    w("Problems where `gate_asdeployed` certifies but `panel_base_2of3` does "
      "not: **%d**%s" % (len(only_gate),
                         (" -> `%s`" % ", ".join(r["sample_id"] for r in only_gate))
                         if only_gate else " (expected 0)"))
    w()

    w("## 3.4 Pair B, three-family level")
    w()
    p3 = [r for r in nd if r["panel_base_3of3"] is not None]
    w("| Gate outcome | problems | base-agreed cert wrong | right |")
    w("|---|---:|---:|---:|")
    b2 = collections.defaultdict(list)
    for r in p3:
        if r["gate_tau"] is not None:
            b2["gate_tau admitted"].append(r)
        elif r["decision"] == "ACCEPT" and r["n_fam"] == 2:
            b2["ACCEPT, resampling reduced to a two-family clique"].append(r)
        elif r["decision"] == "ACCEPT":
            b2["ACCEPT, other (no value or score < 33.3)"].append(r)
        else:
            b2[r["decision"] or "ERROR"].append(r)
    for k in sorted(b2):
        rs = b2[k]
        bad = sum(1 for r in rs if rw(r, "panel_base_3of3") is False)
        good = sum(1 for r in rs if rw(r, "panel_base_3of3") is True)
        w("| %s | %d | %d | %d |" % (k, len(rs), bad, good))
        pair_rows.append(dict(pair="B", bucket=k, n=len(rs), wrong=bad, right=good))
    w("| **total** | **%d** | | |" % len(p3))
    w()
    only_tau = [r for r in nd
                if r["gate_tau"] is not None and r["panel_base_3of3"] is None]
    w("Problems where `gate_tau` admits but `panel_base_3of3` has no "
      "certificate: **%d**%s" % (len(only_tau),
                                 (" -> `%s`" % ", ".join(r["sample_id"] for r in only_tau))
                                 if only_tau else " (expected 0)"))
    w()

    w("## 3.4 host_vote against panel_base_2of3")
    w()
    both = [r for r in nd if r["host_vote"] is not None and r["panel_base_2of3"] is not None]
    vonly = [r for r in nd if r["host_vote"] is not None and r["panel_base_2of3"] is None]
    ponly = [r for r in nd if r["host_vote"] is None and r["panel_base_2of3"] is not None]
    neither = [r for r in nd if r["host_vote"] is None and r["panel_base_2of3"] is None]
    w("| Cell | problems | host_vote wrong | panel_base_2of3 wrong |")
    w("|---|---:|---:|---:|")
    for nm, rs in (("both certify", both), ("host_vote only", vonly),
                   ("panel_base_2of3 only", ponly), ("neither", neither)):
        w("| %s | %d | %s | %s |"
          % (nm, len(rs),
             sum(1 for r in rs if rw(r, "host_vote") is False) if rs else 0,
             sum(1 for r in rs if rw(r, "panel_base_2of3") is False) if rs else 0))
        pair_rows.append(dict(pair="vote_vs_panel2", bucket=nm, n=len(rs),
                              wrong=sum(1 for r in rs if rw(r, "host_vote") is False),
                              right=sum(1 for r in rs if rw(r, "panel_base_2of3") is False)))
    w()
    agree = [r for r in both
             if close(to_num(r["host_vote"]) or 0.0, to_num(r["panel_base_2of3"]) or 0.0)]
    dis = [r for r in both if r not in agree]
    w("Where both certify (%d): the two certificates agree on **%d** and "
      "disagree on **%d**. Among the disagreements, host_vote wrong %d, "
      "panel_base_2of3 wrong %d."
      % (len(both), len(agree), len(dis),
         sum(1 for r in dis if rw(r, "host_vote") is False),
         sum(1 for r in dis if rw(r, "panel_base_2of3") is False)))
    w()

    open(os.path.join(a.out, "03_decomposition.md"), "w",
         encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    with open(os.path.join(a.out, "03_decomposition_problem.csv"), "w",
              encoding="utf-8", newline="") as fh:
        wt = csv.DictWriter(fh, fieldnames=list(prows[0].keys()))
        wt.writeheader(); wt.writerows(prows)
    with open(os.path.join(a.out, "03_pairs.csv"), "w",
              encoding="utf-8", newline="") as fh:
        wt = csv.DictWriter(fh, fieldnames=["pair", "bucket", "n", "wrong", "right"])
        wt.writeheader(); wt.writerows(pair_rows)
    print("wrote 03_decomposition.md, 03_decomposition_problem.csv, 03_pairs.csv")
    print("derived verdicts under", vroot)
    for row in prows:
        print("  %-18s n=%-4d wrong=%-3d" % (row["judge"], row["n_certified"], row["n_wrong"]))
    print("chain cases:", len(chain_cases))
    return 0


if __name__ == "__main__":
    sys.exit(main())
