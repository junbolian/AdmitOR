# -*- coding: utf-8 -*-
"""Tables and audit exports of the runs on human-written texts, from the published records (no model call, no key).

Purpose
    Score the certificates of the published releases of IndustryOR and Mamo ComplexLP (run `humanbench`) and of the
    corrected releases of the OptiMind authors (run `optimind`) with `round_aware` of scripts/score_eval.py, write the
    tables and export every certificate the audit reads.

Inputs (under --records, default artifacts/v2/<run>), per benchmark folder industryor/ and mamo_complex/
    problems.csv     sample_id, source record or row, label (and problem_class in `optimind`)
    workorder.jsonl  problem texts
    verdicts.jsonl   decision of the primary sampler per problem (printed)
    judges.csv       decision and certified value per problem and rule (scripts/rerun_verdicts.py --tau 33.4)
    runs/<id>/       spec.json, A-direct.py, B-structured.py, C-direct.py, verdict_full.json, verdict_independent.json,
                     verification_<A,B,C>.json
    humanbench only: expert/expert_status.csv, the per-problem status derived from the expert audit of Xiao et al.
                     (2025) (scripts/human_expert_status.py)

Outputs
    run humanbench, under --out (default <records>/tables):
        h1_rules, h2_check, h2_check_unparsed, h3_single_vs, h4_joint, h5_expert (.csv and .md), h5_expert_status.csv,
        h6_per_problem.csv
    run optimind, under --out:
        o1_rules, o2_check, o2_check_unparsed (.csv and .md), o3_per_problem.csv
    both runs, under --exports (default <records>):
        misses_3of3.md        every panel_base_3of3 certificate that misses the label
        misses_2of3_only.md   every panel_base_2of3 certificate that misses the label on a problem without a
                              panel_base_3of3 certificate
        withdrawn_matching.md every label-matching panel_base_3of3 certificate that the rule "B or C" withdraws

Scoring
    round_aware(value, label): relative tolerance 1e-4, or equality after rounding the value to the number of decimals
    written in the label. In `optimind` a label written in the source with a zero decimal (219816.0) is stored as the
    integer 219816 (scripts/human_problems.py). Data-verification replies that cannot be parsed after three attempts
    count as not flagged.

Usage (from the repository root)
    python scripts/human_tables.py --run humanbench [--records artifacts/v2/humanbench] [--out ...] [--exports ...]
    python scripts/human_tables.py --run optimind   [--records artifacts/v2/optimind]   [--out ...] [--exports ...]
"""
import argparse
import collections
import csv
import itertools
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_eval import round_aware, to_num  # noqa: E402

ap = argparse.ArgumentParser(description="Tables and exports of the runs on human-written texts.")
ap.add_argument("--run", required=True, choices=["humanbench", "optimind"])
ap.add_argument("--records", default=None)
ap.add_argument("--out", default=None)
ap.add_argument("--exports", default=None)
A = ap.parse_args()
RUN = A.run
REC = A.records or os.path.join("artifacts", "v2", RUN)
OUT = A.out or os.path.join(REC, "tables")
EXP_OUT = A.exports or REC
os.makedirs(OUT, exist_ok=True)
os.makedirs(EXP_OUT, exist_ok=True)

BENCH = ["industryor", "mamo_complex"]
if RUN == "humanbench":
    NAME = {"industryor": "IndustryOR", "mamo_complex": "Mamo ComplexLP", "pooled": "pooled"}
    T = {"rules": "h1_rules", "check": "h2_check", "unparsed": "h2_check_unparsed", "per_problem": "h6_per_problem"}
    LABCOL = "original_label"
else:
    NAME = {"industryor": "OptiMind IndustryOR", "mamo_complex": "OptiMind Mamo-Complex", "pooled": "pooled"}
    T = {"rules": "o1_rules", "check": "o2_check", "unparsed": "o2_check_unparsed", "per_problem": "o3_per_problem"}
    LABCOL = "answer"
CAND = {"A": "A-direct", "B": "B-structured", "C": "C-direct"}
FAMNAME = {"A": "A (DeepSeek-V4-Flash)", "B": "B (GPT-6.1 Sol)", "C": "C (Claude Sonnet 5.5)"}
PROGS = ("A-direct", "B-structured", "C-direct")
LIST_RULES = ("gate", "gate_3fam", "gate_tau", "panel_base_2of3", "panel_base_3of3", "ind_gate", "ind_gate_tau")
TOL = 1e-4


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def jload(p):
    return json.load(open(p, encoding="utf-8")) if os.path.isfile(p) else None


# ------------------------------------------------------------------ records
D = {}
for b in BENCH:
    B = os.path.join(REC, b)
    prob = list(csv.DictReader(open(os.path.join(B, "problems.csv"), encoding="utf-8")))
    ids = [r["sample_id"] for r in prob]
    lab = {r["sample_id"]: json.loads(r["label"]) for r in prob}
    cls = {r["sample_id"]: r.get("problem_class", "") for r in prob}
    q = {r["sample_id"]: r["question"] for r in jl(os.path.join(B, "workorder.jsonl"))}
    dec = {v["sample_id"]: v["decision"] for v in jl(os.path.join(B, "verdicts.jsonl"))}
    J = collections.defaultdict(dict)
    for r in csv.DictReader(open(os.path.join(B, "judges.csv"), encoding="utf-8")):
        if r["decision"] == "ACCEPT" and r["clique_value"] != "":
            J[r["rule"]][r["sample_id"]] = float(r["clique_value"])
    single, status, rep = {f: {} for f in "ABC"}, {f: {} for f in "ABC"}, {f: {} for f in "ABC"}
    for sid in ids:
        vf = jload(os.path.join(B, "runs", sid, "verdict_full.json")) or {}
        ob, st = vf.get("objectives") or {}, vf.get("statuses") or {}
        for f, c in CAND.items():
            o = ob.get(c)
            if isinstance(o, list) and o and o[0] is not None:
                single[f][sid] = float(o[0])
            t = st.get(c)
            status[f][sid] = t[0] if isinstance(t, list) and t else None
            r = jload(os.path.join(B, "runs", sid, "verification_%s.json" % f))
            if r is not None:
                rep[f][sid] = r
    D[b] = dict(ids=ids, lab=lab, cls=cls, q=q, dec=dec, J=J, single=single, status=status, rep=rep)
if RUN == "humanbench":
    EST = {}
    for r in csv.DictReader(open(os.path.join(REC, "expert", "expert_status.csv"), encoding="utf-8")):
        EST[r["sample_id"]] = {"status": r["expert_status"], "original_label": r["original_label"],
                               "expert_label": r["expert_label"] if r["expert_label"] != "" else None,
                               "match": r["match_to_cleaned_file"], "best_jaccard": float(r["best_5gram_jaccard_to_cleaned_file"]),
                               "in_original_expert_file": r["exact_match_in_original_expert_file"], "row": r}


def hit(lab, v):
    return v is not None and bool(round_aware(to_num(v), to_num(lab), lab))


def hitb(b, sid, v):
    return hit(D[b]["lab"][sid], v)


def flags(b, sid, fl):
    rep = D[b]["rep"]
    return {f: bool(rep[f].get(sid) and rep[f][sid].get("status") == "ok" and rep[f][sid].get(fl)) for f in "ABC"}


def bc(b, sid):
    f = flags(b, sid, "flag_any")
    return f["B"] or f["C"]


COMBO = {"C": lambda f: f["C"], "A": lambda f: f["A"], "B": lambda f: f["B"], "B or C": lambda f: f["B"] or f["C"],
         "B and C": lambda f: f["B"] and f["C"]}


def certs(b):
    C = {"single_" + f: D[b]["single"][f] for f in "ABC"}
    for r in ("panel_base_2of3", "panel_base_3of3", "gate_tau"):
        C[r] = D[b]["J"].get(r, {})
    for base in ("panel_base_2of3", "panel_base_3of3"):
        for cmb in ("B or C", "B and C"):
            C["%s + check (%s)" % (base, cmb)] = {s: v for s, v in C[base].items() if not COMBO[cmb](flags(b, s, "flag_any"))}
    return C


def se(k, n):
    return math.sqrt((k / n) * (1 - k / n) / n) if n else None


def f4(x):
    return "" if x is None else "%.4f" % x


def write(name, header, rows, caption):
    with open(os.path.join(OUT, name + ".csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    md = [caption, "", "| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    md += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    open(os.path.join(OUT, name + ".md"), "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")


# ------------------------------------------------------------------ rules (h1 / o1)
RULES = ["single_A", "single_B", "single_C", "panel_base_2of3", "panel_base_3of3", "gate_tau",
         "panel_base_2of3 + check (B or C)", "panel_base_3of3 + check (B or C)", "panel_base_3of3 + check (B and C)"]
CERT = {b: certs(b) for b in BENCH}
rows = []
for rule in RULES:
    pool = [0, 0, 0]
    for b in BENCH:
        c = CERT[b][rule]
        n, m = len(c), sum(hitb(b, s, v) for s, v in c.items())
        N = len(D[b]["ids"])
        pool = [pool[0] + N, pool[1] + n, pool[2] + m]
        rows.append([NAME[b], rule, N, n, f4(n / N), f4(se(n, N)), m, n - m, f4(m / n if n else None), f4(se(m, n))])
    N, n, m = pool
    rows.append(["pooled", rule, N, n, f4(n / N), f4(se(n, N)), m, n - m, f4(m / n if n else None), f4(se(m, n))])
rows.sort(key=lambda r: ([NAME["industryor"], NAME["mamo_complex"], "pooled"].index(r[0]), RULES.index(r[1])))
CAP1_REST = ("Coverage = certificates / problems (an ERROR counts as not certified). Binomial standard errors. single_X: family X's "
             "program value at the stated instance; gate_tau: three-family agreement on resampled instances (tau 33.4); `+ check`: "
             "withdrawn when the named families raise flag_any in the data verification (unparsed replies count as not flagged).")
if RUN == "humanbench":
    cap1 = "Table h1. Certification rules on the human-written benchmarks, scored with `round_aware` of scripts/score_eval.py. " + CAP1_REST
else:
    cap1 = ("Table o1. Certification rules on the OptiMind cleaned IndustryOR and Mamo-Complex, scored with `round_aware` of "
            "scripts/score_eval.py against the OptiMind answers. " + CAP1_REST)
write(T["rules"], ["benchmark", "rule", "problems", "certificates", "coverage", "coverage_se", "label_matches", "label_misses",
                   "precision", "precision_se"], rows, cap1)

# ------------------------------------------------------------------ check (h2 / o2)
rows, rowsu = [], []
for b in BENCH + ["pooled"]:
    bs = BENCH if b == "pooled" else [b]
    for cmb in COMBO:
        for fl in ("flag_mismatch", "flag_not_stated", "flag_any"):
            c = [0, 0, 0, 0]
            n = 0
            for bb in bs:
                for s, v in CERT[bb]["panel_base_3of3"].items():
                    n += 1
                    c[(0 if COMBO[cmb](flags(bb, s, fl)) else 2) + (0 if hitb(bb, s, v) else 1)] += 1
            rows.append([NAME[b], cmb, fl, n] + c)
    for f in "CAB":
        rs = [r for bb in bs for r in D[bb]["rep"][f].values()]
        rowsu.append([NAME[b], f, len(rs), sum(1 for r in rs if r.get("status") != "ok"),
                      sum(1 for r in rs if len(r.get("attempts") or []) > 1)])
p = "h2" if RUN == "humanbench" else "o2"
write(T["check"], ["benchmark", "families", "flag", "certificates", "flagged_match", "flagged_miss", "not_flagged_match",
                   "not_flagged_miss"], rows,
      "Table %s. Data-verification flags against label match among the panel_base_3of3 certificates (`round_aware`%s). "
      "Unparsed replies (after up to three attempts) count as not flagged." % (p, "" if RUN == "humanbench" else ", OptiMind answers"))
write(T["unparsed"], ["benchmark", "family", "replies", "unparsed_after_retries", "replies_needing_more_than_one_attempt"], rowsu,
      "Table %sb. Data-verification replies per family: unparsed after up to three attempts, and replies that needed a retry." % p)

if RUN == "humanbench":
    # -------------------------------------------------------------- h3
    rows = []
    for b in BENCH + ["pooled"]:
        bs = BENCH if b == "pooled" else [b]
        for f in "ABC":
            n = m = rest = 0
            for bb in bs:
                for s in D[bb]["ids"]:
                    if s in CERT[bb]["panel_base_3of3"]:
                        continue
                    rest += 1
                    v = D[bb]["single"][f].get(s)
                    if v is not None:
                        n += 1
                        m += not hitb(bb, s, v)
            rows.append([NAME[b], f, rest, n, n - m, m, f4((n - m) / n if n else None)])
    write("h3_single_vs", ["benchmark", "family", "problems_without_panel_base_3of3", "values_returned", "label_matches", "label_misses",
                           "precision"], rows,
          "Table h3. On the problems without a panel_base_3of3 certificate: the values each family's program returns at the stated "
          "instance and how many miss the label (`round_aware`).")
    # -------------------------------------------------------------- h4
    rows = []
    for b in BENCH + ["pooled"]:
        bs = BENCH if b == "pooled" else [b]
        N = sum(len(D[bb]["ids"]) for bb in bs)
        k = {f: sum(1 for bb in bs for s in D[bb]["ids"] if hitb(bb, s, D[bb]["single"][f].get(s))) for f in "ABC"}
        allm = sum(1 for bb in bs for s in D[bb]["ids"] if all(hitb(bb, s, D[bb]["single"][f].get(s)) for f in "ABC"))
        pr = {f: k[f] / N for f in "ABC"}
        rows.append([NAME[b], N, k["A"], f4(pr["A"]), k["B"], f4(pr["B"]), k["C"], f4(pr["C"]), f4(pr["A"] * pr["B"] * pr["C"]), allm,
                     f4(allm / N)])
    write("h4_joint", ["benchmark", "problems", "A_matches", "A_share", "B_matches", "B_share", "C_matches", "C_share",
                       "product_of_shares", "all_three_match", "all_three_share"], rows,
          "Table h4. Share of problems on which each family's program value at the stated instance matches the label "
          "(`round_aware`; no value counts as no match), the product of the three shares, and the share on which all three match.")
    # -------------------------------------------------------------- h5
    STAT = ["removed", "kept, same label", "kept, label changed"]
    H5S = ["benchmark", "sample_id", "expert_status", "original_label", "expert_label", "match_to_cleaned_file",
           "best_5gram_jaccard_to_cleaned_file", "exact_match_in_original_expert_file"]
    with open(os.path.join(OUT, "h5_expert_status.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(H5S)
        for b in BENCH:
            for sid in D[b]["ids"]:
                w.writerow([NAME[b]] + [EST[sid]["row"][k] for k in H5S[1:]])
    xrows = []
    for scope in BENCH + ["pooled"]:
        bs = BENCH if scope == "pooled" else [scope]
        for rule in ("panel_base_3of3", "panel_base_3of3 + check (B or C)"):
            for st in STAT:
                n = m = mn = 0
                for b in bs:
                    for sid, v in D[b]["J"]["panel_base_3of3"].items():
                        if rule != "panel_base_3of3" and bc(b, sid):
                            continue
                        s = EST[sid]
                        if s["status"] != st:
                            continue
                        n += 1
                        m += hit(s["original_label"], v)
                        if st == "kept, label changed":
                            mn += hit(s["expert_label"], v)
                xrows.append([NAME.get(scope, "pooled"), rule, st, n, m, n - m, mn if st == "kept, label changed" else ""])
    cnt = []
    for scope in BENCH + ["pooled"]:
        bs = BENCH if scope == "pooled" else [scope]
        c = collections.Counter(EST[s]["status"] for b in bs for s in D[b]["ids"])
        cnt.append([NAME.get(scope, "pooled"), sum(c.values())] + [c.get(s, 0) for s in STAT])
    H5 = ["benchmark", "rule", "expert_status", "certificates", "match_original_label", "miss_original_label", "match_new_label"]
    with open(os.path.join(OUT, "h5_expert.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(H5)
        w.writerows(xrows)
    md = ["Table h5. Certificates against the expert audit of Xiao et al. (2025) (cleaned IndustryOR and Mamo ComplexLP of the "
          "LLM4OR portal, `expert/SOURCE.md`). A problem is matched to the cleaned file by question text after lowercasing and "
          "collapsing whitespace; a problem without an exact match counts as removed by the audit. Label comparison with "
          "`round_aware` of scripts/score_eval.py. `match_new_label`: for problems whose label the audit changed, certificates "
          "that match the new label.", "",
          "| " + " | ".join(H5) + " |", "|" + "---|" * len(H5)]
    md += ["| " + " | ".join(str(x) for x in r) + " |" for r in xrows]
    md += ["", "Expert status of all problems:", "", "| benchmark | problems | removed | kept, same label | kept, label changed |",
           "|---|---:|---:|---:|---:|"]
    md += ["| " + " | ".join(str(x) for x in r) + " |" for r in cnt]
    chg = [(b, sid, EST[sid]) for b in BENCH for sid in D[b]["ids"] if EST[sid]["status"] == "kept, label changed"]
    md += ["", "Problems whose label the audit changed:", "", "| benchmark | problem | original label | expert label | panel_base_3of3 value |",
           "|---|---|---:|---:|---:|"]
    md += ["| %s | `%s` | %s | %s | %s |" % (NAME[b], sid, s["original_label"], s["expert_label"],
                                            D[b]["J"]["panel_base_3of3"].get(sid, "no certificate")) for b, sid, s in chg]
    nox = [(b, sid, EST[sid]) for b in BENCH for sid in D[b]["ids"] if EST[sid]["match"] != "exact"]
    md += ["", "Problems without an exact match in the cleaned file (%d; all counted as removed). Best word 5-gram Jaccard "
           "against any cleaned record: maximum %.4f." % (len(nox), max((s["best_jaccard"] for _, _, s in nox), default=0.0)), "",
           "| benchmark | problem | best 5-gram Jaccard |", "|---|---|---:|"]
    md += ["| %s | `%s` | %.4f |" % (NAME[b], sid, s["best_jaccard"]) for b, sid, s in nox]
    open(os.path.join(OUT, "h5_expert.md"), "w", encoding="utf-8", newline="\n").write("\n".join(md) + "\n")

# ------------------------------------------------------------------ per problem (h6 / o3)


def pstatus(s):
    if s == "optimal":
        return "optimal"
    if isinstance(s, str) and s.startswith("crash"):
        return "crash"
    if isinstance(s, str) and ("infeasible" in s or "unbounded" in s or s in ("no_feasible_solution", "no_solution")):
        return "infeasible_or_unbounded"
    return "error"


def num(x):
    return "" if x is None else repr(float(x))


PRULES = ["panel_base_2of3", "panel_base_3of3", "gate_tau", "ind_gate_tau"]
cols = ["benchmark", "sample_id", LABCOL] + (["problem_class"] if RUN == "optimind" else []) + [
    "value_A", "value_B", "value_C", "status_A", "status_B", "status_C"] + PRULES + [
    "flag_any_A", "flag_any_B", "flag_any_C", "withdrawn_B_or_C", "withdrawn_B_and_C"]
with open(os.path.join(OUT, T["per_problem"] + ".csv"), "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, cols, lineterminator="\n")
    w.writeheader()
    for b in BENCH:
        for s in D[b]["ids"]:
            row = {"benchmark": b, "sample_id": s, LABCOL: D[b]["lab"][s]}
            if RUN == "optimind":
                row["problem_class"] = D[b]["cls"][s]
            for f in "ABC":
                row["value_" + f] = num(D[b]["single"][f].get(s))
                row["status_" + f] = pstatus(D[b]["status"][f].get(s))
            for rule in PRULES:
                row[rule] = num(D[b]["J"].get(rule, {}).get(s))
            fl = {}
            for f in "ABC":
                r = D[b]["rep"][f].get(s)
                fl[f] = "" if r is None else ("unparsed" if r.get("status") != "ok" else str(bool(r.get("flag_any"))))
                row["flag_any_" + f] = fl[f]
            has = row["panel_base_3of3"] != ""
            row["withdrawn_B_or_C"] = str(fl["B"] == "True" or fl["C"] == "True") if has else ""
            row["withdrawn_B_and_C"] = str(fl["B"] == "True" and fl["C"] == "True") if has else ""
            w.writerow(row)


# ------------------------------------------------------------------ exports
def fence(t, lang=""):
    n = 3
    while "`" * n in t:
        n += 1
    return "`" * n + lang + "\n" + t.rstrip("\n") + "\n" + "`" * n


def fmt(x):
    if isinstance(x, float) and x.is_integer():
        return str(x)
    return repr(x) if x is not None else "none"


def close(a, c):
    return abs(a - c) <= TOL * max(1.0, abs(a), abs(c))


def flagtxt(b, sid, f):
    r = D[b]["rep"][f].get(sid)
    if not r:
        return "no reply"
    if r.get("status") != "ok":
        return "unparsed"
    return "flag_any %s (mismatch %s, not_stated %s)" % (r.get("flag_any"), r.get("flag_mismatch"), r.get("flag_not_stated"))


SRCFILE = {"industryor": "industryor.jsonl", "mamo_complex": "mamo_complex_test.jsonl"}
CSVFILE = {"industryor": "optimind_cleaned_classified_industryor.csv", "mamo_complex": "optimind_cleaned_classified_mamo_complex.csv"}


def section(k, b, sid, rule, full):
    rd = os.path.join(REC, b, "runs", sid)
    qtext, lab = D[b]["q"][sid], D[b]["lab"][sid]
    acc = {r: D[b]["J"][r][sid] for r in LIST_RULES if sid in D[b]["J"].get(r, {})}
    v = jload(os.path.join(rd, "verdict_full.json"))
    ob = v.get("objectives") or {}
    v0 = {f: (float(ob[c][0]) if isinstance(ob.get(c), list) and ob[c] and ob[c][0] is not None else None) for f, c in CAND.items()}
    pairs = [(x, y) for x, y in itertools.combinations([f for f in "ABC" if v0[f] is not None], 2) if close(v0[x], v0[y])]
    mn, mx = bool(re.search(r"\bminim", qtext, re.I)), bool(re.search(r"\bmaxim", qtext, re.I))
    sense = "min" if mn and not mx else "max" if mx and not mn else "not determined from the problem text"
    o = ["## %d. %s (%s)" % (k, sid, NAME[b]), "", "### 1. Identification", "", "| Field | Value |", "|---|---|", "| Sample id | `%s` |" % sid]
    if RUN == "humanbench":
        s = EST[sid]
        o += ["| Benchmark | %s (`datasets/benchmark/%s`, field `index` = %s) |" % (NAME[b], SRCFILE[b], sid.split("_")[-1]),
              "| Optimization sense | %s (words \"minim...\" / \"maxim...\" in the problem text) |" % sense,
              "| Certified value (%s) | %s |" % (rule, fmt(acc.get(rule))), "| Label (original benchmark) | %s |" % lab,
              "| Rules that certify it | %s |" % (", ".join("%s %s" % (r, fmt(x)) for r, x in acc.items()) or "none"),
              "| Expert status (Xiao et al. 2025) | %s%s |" % (s["status"], "; expert label %s" % s["expert_label"] if s["expert_label"] is not None else ""),
              "| Families agreeing at instance 0 | %s |" % (", ".join("%s and %s" % (FAMNAME[x], FAMNAME[y]) for x, y in pairs) or "none")]
    else:
        o += ["| Benchmark | %s (`datasets/optimind_corrected/%s`, 0-based row %s) |" % (NAME[b], CSVFILE[b], sid.split("_")[-1]),
              "| Problem class (OptiMind) | %s |" % D[b]["cls"][sid].replace("|", "\\|"),
              "| Optimization sense | %s (words \"minim...\" / \"maxim...\" in the problem text) |" % sense,
              "| Certified value (%s) | %s |" % (rule, fmt(acc.get(rule))), "| Answer (OptiMind) | %s |" % lab,
              "| Rules that certify it | %s |" % (", ".join("%s %s" % (r, fmt(x)) for r, x in acc.items()) or "none"),
              "| Families agreeing at instance 0 | %s |" % (", ".join("%s and %s" % (FAMNAME[x], FAMNAME[y]) for x, y in pairs) or "none")]
        o += ["| Verification, family %s | %s |" % (FAMNAME[f], flagtxt(b, sid, f)) for f in "ABC"]
    o += ["", "### 2. Problem text", "", fence(qtext), ""]
    n = 3
    if full:
        sp = jload(os.path.join(rd, "spec.json"))
        lines = ["\"%s\": %s" % (nm, json.dumps(x, ensure_ascii=False, separators=(",", ":"))) for nm, x in (sp.get("spec") or {}).items()]
        o += ["### 3. Extracted parameter set (`spec.json`: `spec` and `warnings`)", "", fence("\n".join(lines), "json"), "", "Warnings:", "",
              fence("\n".join(sp.get("warnings") or []) or "none"), "", "Extraction attempts: %d." % len(sp.get("extraction_attempts") or [1]),
              "", "### 4. Programs", ""]
        for pg in PROGS:
            pp = os.path.join(rd, pg + ".py")
            o += ["#### %s.py" % pg, "", fence(open(pp, encoding="utf-8").read() if os.path.isfile(pp) else "(no program file)", "python"), ""]
        o += ["### 5. Values on the stated and resampled instances", ""]
        for name, fn in (("param_screen", "verdict_full.json"), ("independent", "verdict_independent.json")):
            vv = jload(os.path.join(rd, fn))
            ob, st = vv.get("objectives") or {}, vv.get("statuses") or {}
            m = max((len(x) for x in ob.values()), default=0)
            o += ["#### %s" % name, "", "Decision: %s; clique %s; informative instances %s. Instance 0 is the stated instance." % (
                vv["decision"], ", ".join(vv.get("clique") or []) or "none", vv.get("informative")), "",
                  "| Instance | " + " | ".join(PROGS) + " |", "|---|" + "---|" * len(PROGS)]
            for i in range(m):
                cells = []
                for pg in PROGS:
                    a, sts = ob.get(pg, []), st.get(pg, [])
                    stx = str(sts[i] if i < len(sts) else None).replace("|", "\\|").replace("\r", " ").replace("\n", " ")
                    cells.append("%s (%s)" % (fmt(a[i]) if i < len(a) else "none", stx))
                o.append("| %s | " % ("0 (stated)" if i == 0 else str(i)) + " | ".join(cells) + " |")
            o.append("")
        n = 6
    o += ["### %d. Data-verification replies" % n, ""]
    for f in "ABC":
        r = D[b]["rep"][f].get(sid)
        if not r:
            o += ["#### Family %s" % FAMNAME[f], "", "No reply.", ""]
            continue
        o += ["#### Family %s" % FAMNAME[f], "", "Status %s; attempts %d; flag_mismatch %s; flag_not_stated %s; flag_any %s." % (
            r.get("status"), len(r.get("attempts") or [1]), r.get("flag_mismatch"), r.get("flag_not_stated"), r.get("flag_any")), "",
              fence(r.get("reply") or "", "json"), ""]
    return "\n".join(o) + "\n"


def export(fname, title, intro, items, rule, full):
    if RUN == "humanbench":
        head = ["# " + title, "", intro, "", "| Sample id | Benchmark | Certified value | Label | Expert status | B or C flags |",
                "|---|---|---:|---:|---|---|"]
        for b, sid in items:
            s = EST[sid]
            head.append("| `%s` | %s | %s | %s | %s | %s |" % (sid, NAME[b], fmt(D[b]["J"][rule].get(sid)), D[b]["lab"][sid],
                                                              s["status"] + ("; expert label %s" % s["expert_label"] if s["expert_label"] is not None else ""),
                                                              "yes" if bc(b, sid) else "no"))
    else:
        head = ["# " + title, "", intro, "", "| Sample id | Benchmark | Problem class | Certified value | Answer | B or C flags |",
                "|---|---|---|---:|---:|---|"]
        for b, sid in items:
            head.append("| `%s` | %s | %s | %s | %s | %s |" % (sid, NAME[b], D[b]["cls"][sid].replace("|", "\\|"), fmt(D[b]["J"][rule].get(sid)),
                                                              D[b]["lab"][sid], "yes" if bc(b, sid) else "no"))
    body = [section(k, b, sid, rule, full) for k, (b, sid) in enumerate(items, 1)]
    text = "\n".join(head) + "\n\n" + "\n".join(body)
    text = re.sub(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/](?=(?:Python|AdmitOR|Users|OptSkills|ProgramData|Program|Windows|tmp|Temp))"
                  r"(?:[^\\/\"'\s<>|`]+[\\/])*", "<PATH>/", text)
    if re.search(r"(?<![A-Za-z0-9])[A-Z]:[\\/](?=Users|AdmitOR|Python)|sk-[A-Za-z0-9]{16,}", text):
        raise SystemExit("absolute path or key-like string in " + fname)
    open(os.path.join(EXP_OUT, fname), "w", encoding="utf-8", newline="\n").write(text)
    return len(items), os.path.getsize(os.path.join(EXP_OUT, fname))


def key(sid):
    return int(sid.split("_")[-1])


m3 = [(b, sid) for b in BENCH for sid in sorted(D[b]["J"]["panel_base_3of3"], key=key) if not hitb(b, sid, D[b]["J"]["panel_base_3of3"][sid])]
m2 = [(b, sid) for b in BENCH for sid in sorted(D[b]["J"]["panel_base_2of3"], key=key)
      if not hitb(b, sid, D[b]["J"]["panel_base_2of3"][sid]) and sid not in D[b]["J"]["panel_base_3of3"]]
wd = [(b, sid) for b in BENCH for sid in sorted(D[b]["J"]["panel_base_3of3"], key=key)
      if hitb(b, sid, D[b]["J"]["panel_base_3of3"][sid]) and bc(b, sid)]
if RUN == "humanbench":
    COMMON = ("IndustryOR and Mamo ComplexLP, scored with `round_aware` of scripts/score_eval.py against the "
              "original labels. Sections: identification with the expert status of Xiao et al. (2025), problem text, extracted "
              "parameter set with warnings, the three programs, values on the stated and resampled instances (both samplers), and "
              "the data-verification replies of the three families.")
    r1 = export("misses_3of3.md", "panel_base_3of3 certificates that miss the original label",
                "Every panel_base_3of3 certificate whose value misses the label. " + COMMON, m3, "panel_base_3of3", True)
    r2 = export("misses_2of3_only.md", "panel_base_2of3 certificates that miss the label and are not panel_base_3of3 certificates",
                "Every panel_base_2of3 certificate whose value misses the label on a problem without a panel_base_3of3 certificate. " + COMMON,
                m2, "panel_base_2of3", True)
    r3 = export("withdrawn_matching.md", "Label-matching panel_base_3of3 certificates withdrawn by the rule B or C",
                "Every panel_base_3of3 certificate whose value matches the label and that the rule \"B or C\" withdraws (family B or C "
                "raises flag_any). " + COMMON, wd, "panel_base_3of3", True)
else:
    COMMON = ("OptiMind cleaned IndustryOR and Mamo-Complex (`datasets/optimind_corrected/SOURCE.md`), scored with `round_aware` of "
              "scripts/score_eval.py against the OptiMind answers.")
    FULL = (" Sections: identification, problem text, extracted parameter set with warnings, the three programs, values on the "
            "stated and resampled instances (both samplers), and the data-verification replies of the three families.")
    r1 = export("misses_3of3.md", "panel_base_3of3 certificates that miss the OptiMind answer",
                "Every panel_base_3of3 certificate whose value misses the answer. " + COMMON + FULL, m3, "panel_base_3of3", True)
    r2 = export("misses_2of3_only.md", "panel_base_2of3 certificates that miss the OptiMind answer and are not panel_base_3of3 certificates",
                "Every panel_base_2of3 certificate whose value misses the answer on a problem without a panel_base_3of3 certificate. "
                + COMMON + FULL, m2, "panel_base_2of3", True)
    r3 = export("withdrawn_matching.md", "Answer-matching panel_base_3of3 certificates withdrawn by the rule B or C",
                "Every panel_base_3of3 certificate whose value matches the answer and that the rule \"B or C\" withdraws (family B or C "
                "raises flag_any). " + COMMON + " Sections: identification with the flags of the three families, problem text, and the "
                "data-verification replies.", wd, "panel_base_3of3", False)
print("decisions:", json.dumps({NAME[b]: dict(collections.Counter(D[b]["dec"].values())) for b in BENCH}))
print("exports (problems, bytes):", json.dumps({"misses_3of3": r1, "misses_2of3_only": r2, "withdrawn_matching": r3}))
print("tables written to", OUT)
