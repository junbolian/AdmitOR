# -*- coding: utf-8 -*-
"""Withdrawal rules on the data-verification flags under one scoring rule (no model call).

Purpose
    For the two OptMATH sets, score the panel_base_3of3 and panel_base_2of3 certificates with
    round_aware (scripts/score_eval.py) and compare six withdrawal rules: a certificate is withdrawn
    when family B or C flags (the rule of the paper), B and C, C, B, A, or at least two of A, B, C.
    Item 1 gives certificates, misses and precision before and after each rule (flag_any); item 2
    the 2x2 tables of flag against label match for flag_mismatch, flag_not_stated and flag_any.
    An unparsed reply, an API error or a missing reply counts as not flagged. OptMATH-295 excludes
    sample_1 to sample_5.

Inputs
    --records   artifacts/v2 (default): optmath_295 and optmath_200 with problems.csv, judges.csv and
                runs/<id>/verification_<family>.json

Outputs
    <out>/rules_compare.md and <out>/rules_compare.json (default out: artifacts/v2/tables)

Usage (from the repository root)
    python scripts/rules_compare.py [--records artifacts/v2] [--out artifacts/v2/tables]
"""
import argparse
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_eval import round_aware, to_num  # noqa: E402

SETS = {"OptMATH-295": "optmath_295", "OptMATH-200": "optmath_200"}
CERT = ("panel_base_3of3", "panel_base_2of3")
RULES = ("B or C", "B and C", "C", "B", "A", "at least two of A, B, C")
FLAGS = ("flag_mismatch", "flag_not_stated", "flag_any")


def fired(rule, f):
    if rule == "B or C":
        return f["B"] or f["C"]
    if rule == "B and C":
        return f["B"] and f["C"]
    if rule in ("A", "B", "C"):
        return f[rule]
    return sum(f.values()) >= 2


def main():
    ap = argparse.ArgumentParser(description="Withdrawal rules on the data-verification flags.")
    ap.add_argument("--records", default=os.path.join("artifacts", "v2"))
    ap.add_argument("--out", default=os.path.join("artifacts", "v2", "tables"))
    a = ap.parse_args()
    res, md = {}, ["# Withdrawal rules on the data-verification flags, one scoring rule (round_aware)", ""]
    for name, d in SETS.items():
        base = os.path.join(a.records, d)
        lab = {r["sample_id"]: r["label"] for r in csv.DictReader(open(os.path.join(base, "problems.csv"), encoding="utf-8"))}
        rep = {f: {} for f in "ABC"}
        for sid in lab:
            for f in "ABC":
                p = os.path.join(base, "runs", sid, "verification_%s.json" % f)
                if os.path.isfile(p):
                    rep[f][sid] = json.load(open(p, encoding="utf-8"))
        res[name] = {"unparsed_or_error": {f: sum(1 for r in rep[f].values() if r.get("status") != "ok") for f in "CAB"},
                     "replies": {f: len(rep[f]) for f in "CAB"}, "cert": {}}
        judges = list(csv.DictReader(open(os.path.join(base, "judges.csv"), encoding="utf-8")))
        for cert in CERT:
            acc = {}
            for r in judges:
                if r["rule"] == cert and r["decision"] == "ACCEPT" and r["clique_value"] != "":
                    sid = r["sample_id"]
                    acc[sid] = bool(round_aware(to_num(float(r["clique_value"])), to_num(lab[sid]), lab[sid]))
            flags = {sid: {fl: {f: bool(rep[f].get(sid) and rep[f][sid].get("status") == "ok" and rep[f][sid].get(fl))
                                for f in "CAB"} for fl in FLAGS} for sid in acc}
            n, miss = len(acc), sum(not h for h in acc.values())
            dd = {"certificates": n, "misses": miss, "precision": round((n - miss) / n, 4),
                  "missing_reply": {f: sum(1 for sid in acc if sid not in rep[f]) for f in "CAB"}, "rules": {}}
            for rule in RULES:
                keep = [h for sid, h in acc.items() if not fired(rule, flags[sid]["flag_any"])]
                n2, m2 = len(keep), sum(not h for h in keep)
                row = {"certificates_after": n2, "misses_after": m2, "precision_after": round((n2 - m2) / n2, 4) if n2 else None,
                       "withdrawn": n - n2, "withdrawn_miss": miss - m2}
                for fl in FLAGS:
                    c = [0, 0, 0, 0]
                    for sid, h in acc.items():
                        c[(0 if fired(rule, flags[sid][fl]) else 2) + (0 if h else 1)] += 1
                    row[fl] = c
                dd["rules"][rule] = row
            res[name]["cert"][cert] = dd
    for name in SETS:
        md += ["## %s" % name, "", "### Before and after each rule (flag_any; round_aware)", "",
               "| Certified by | Rule (withdrawn when) | Certificates | Misses | Precision | Withdrawn (of which misses) | Certificates after | Misses after | Precision after |",
               "|---|---|---:|---:|---:|---|---:|---:|---:|"]
        for cert in CERT:
            dd = res[name]["cert"][cert]
            for rule in RULES:
                r = dd["rules"][rule]
                md.append("| %s | %s | %d | %d | %.4f | %d (%d) | %d | %d | %.4f |" % (
                    cert, rule + (" (rule of the paper)" if rule == "B or C" else ""), dd["certificates"], dd["misses"],
                    dd["precision"], r["withdrawn"], r["withdrawn_miss"], r["certificates_after"], r["misses_after"], r["precision_after"]))
        for fl in FLAGS:
            md += ["", "### 2x2, %s (flagged & match / flagged & miss / not flagged & match / not flagged & miss)" % fl, "",
                   "| Certified by | n | " + " | ".join(RULES) + " |", "|---|---:|" + "---|" * len(RULES)]
            for cert in CERT:
                dd = res[name]["cert"][cert]
                md.append("| %s | %d | " % (cert, dd["certificates"]) + " | ".join(" / ".join(map(str, dd["rules"][r][fl])) for r in RULES) + " |")
        md += ["", "Replies not ok (unparsed or API error) per family: %s; replies per family: %s." % (
            ", ".join("%s %d" % kv for kv in res[name]["unparsed_or_error"].items()),
            ", ".join("%s %d" % kv for kv in res[name]["replies"].items())), ""]
    os.makedirs(a.out, exist_ok=True)
    open(os.path.join(a.out, "rules_compare.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")
    with open(os.path.join(a.out, "rules_compare.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(res, fh, indent=1)
        fh.write("\n")
    print("wrote", os.path.join(a.out, "rules_compare.md"))


if __name__ == "__main__":
    main()
