# -*- coding: utf-8 -*-
"""Judge ablation additions (zero token); appends to 03_decomposition.md.

(a) K4 value-exclusions split into base-visible and resample-only.
(b) The five base-unanimous problems whose candidates diverged on resampling.
(c) Identity of the gate certificate and the panel_base_3of3 certificate on
    the 138 gate_tau problems.

Inputs
    --runs   artifacts/e1/certify_runs (in git)
    --vault  datasets/vault/optmath-train-300-labels.jsonl (in git)
    --out    default reanalysis/reviewer_round; the script appends to
             <out>/03_decomposition.md when present

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

Reproduce (from the repository root)
    python scripts/task3_additions.py

Outputs
    appended sections of <out>/03_decomposition.md; counts on stdout

Paper location
    Section 4.2 Table 3 and Appendix C "Judge ablation details".
"""
from __future__ import annotations
import argparse, collections, itertools, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_eval import round_aware, to_num

TOL = 1e-4
DEV = {"sample_%d" % i for i in (1, 2, 3, 4, 5)}
ORDER = ["A-direct", "B-structured", "C-direct"]


def close(a, b):
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="artifacts/e1/certify_runs")
    ap.add_argument("--vault", default="datasets/vault/optmath-train-300-labels.jsonl")
    ap.add_argument("--out", default="reanalysis/reviewer_round")
    a = ap.parse_args()

    vault = {}
    for line in open(a.vault, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            vault["sample_%s" % r["idx"]] = str(r.get("answer"))

    excl = collections.defaultdict(lambda: collections.Counter())
    diverged, ident_ok, ident_bad, n_tau = [], 0, [], 0

    for d in sorted(os.listdir(a.runs)):
        p = os.path.join(a.runs, d, "verdict_full.json")
        if not os.path.isfile(p) or d in DEV:
            continue
        v = json.load(open(p, encoding="utf-8"))
        objs = v.get("objectives") or {}
        clique = v.get("clique") or []
        dec = str(v.get("decision", "")).upper()
        fams = {str(m)[:1] for m in clique}
        score = 10.0 * len(fams) + len(clique) + len(v.get("informative") or []) / 10.0

        def base(c):
            s = objs.get(c)
            return float(s[0]) if isinstance(s, list) and s and s[0] is not None else None

        bv = {c: base(c) for c in ORDER if base(c) is not None}

        # (a) split value exclusions
        if clique:
            cb = base(clique[0])
            for c in ORDER:
                if c in clique or c not in bv:
                    continue
                if cb is None:
                    continue
                excl[c]["base-visible" if not close(bv[c], cb) else "resample-only"] += 1

        # (b) base-unanimous but gate did not keep all three
        if len(bv) == 3 and all(close(bv[x], bv[y]) for x, y in itertools.combinations(ORDER, 2)):
            if dec == "ABSTAIN" or (dec == "ACCEPT" and len(fams) == 2):
                out = [c for c in ORDER if c not in clique]
                ans = vault.get(d)
                cert = bv[ORDER[0]]
                diverged.append(dict(
                    sid=d, decision=dec, dropped=out,
                    diagnosis=" | ".join(str(v.get("diagnoses", {}).get(c, ""))[:190] for c in out),
                    disagreements=" | ".join(str(x)[:190] for x in (v.get("disagreements") or [])),
                    base=cert,
                    vault=ans,
                    vault_confirms=(round_aware(to_num(cert), to_num(ans), ans)
                                    if ans is not None else None)))
            # (c) identity on gate_tau problems
            if dec == "ACCEPT" and score >= 33.3 and clique:
                n_tau += 1
                gc = base(clique[0])
                if gc is not None and close(gc, bv[ORDER[0]]):
                    ident_ok += 1
                else:
                    ident_bad.append((d, gc, bv[ORDER[0]]))

    L = ["", "## 3 addition (a). K4 value exclusions, base-visible against resample-only", "",
         "A candidate that solved but was excluded from the clique is "
         "`base-visible` when its stated-instance value already differs from the "
         "clique's, and `resample-only` when it agrees at the stated instance "
         "and diverges only on a resampled one.", "",
         "| Arm | base-visible | resample-only | total |", "|---|---:|---:|---:|"]
    tb = tr = 0
    for c in ORDER:
        b, r = excl[c]["base-visible"], excl[c]["resample-only"]
        tb += b; tr += r
        L.append("| `%s` | %d | %d | %d |" % (c, b, r, b + r))
    L += ["| **total** | **%d** | **%d** | **%d** |" % (tb, tr, tb + tr), ""]

    L += ["## 3 addition (b). Base-unanimous problems whose candidates diverged on resampling", "",
          "| Problem | gate decision | dropped | base value | vault | vault confirms base cert |",
          "|---|---|---|---|---|---|"]
    for r in diverged:
        L.append("| %s | %s | %s | %s | %s | %s |"
                 % (r["sid"], r["decision"], ", ".join(r["dropped"]),
                    r["base"], r["vault"], r["vault_confirms"]))
    L.append("")
    for r in diverged:
        L += ["**%s** diagnosis: `%s`" % (r["sid"], r["diagnosis"] or "(none)"), ""]
        if r["disagreements"]:
            L += ["**%s** disagreements: `%s`" % (r["sid"], r["disagreements"]), ""]
    conf = [r["vault_confirms"] for r in diverged]
    L += ["Vault confirms the base certificate in %d of %d cases."
          % (sum(1 for x in conf if x), len(conf)), ""]

    L += ["## 3 addition (c). Certificate identity on the gate_tau problems", "",
          "| Check | Value |", "|---|---:|",
          "| gate_tau problems that are base-unanimous | %d |" % n_tau,
          "| gate certificate equals the panel_base_3of3 certificate | %d |" % ident_ok,
          "| mismatches | %d |" % len(ident_bad), ""]
    if ident_bad:
        for d, g, p3 in ident_bad:
            L.append("- `%s`: gate %s, panel %s" % (d, g, p3))
        L.append("")

    p = os.path.join(a.out, "03_decomposition.md")
    with open(p, "a", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("appended to", p)
    print("(a) base-visible=%d resample-only=%d" % (tb, tr))
    print("(b) diverged cases: %d, vault confirms base cert in %d"
          % (len(diverged), sum(1 for x in conf if x)))
    print("(c) tau problems=%d identical=%d mismatch=%d" % (n_tau, ident_ok, len(ident_bad)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
