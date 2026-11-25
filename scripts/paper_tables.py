# -*- coding: utf-8 -*-
"""Every table of the paper from the published run records (no model call, no key).

Purpose
    Recompute the certification, audit, data-verification, two-programs-per-family,
    admission, downstream and cost tables from the per-problem records under
    artifacts/v2, and export the two-family-only label misses.

Inputs (all under --records, default artifacts/v2)
    optmath_295, optmath_200, nanoco_150, nanoco_95   problems.csv, verdicts.jsonl, judges.csv,
                                                      workorder.jsonl, runs/<id>/
    optmath_295_k2, nanoco_95_k2                      problems.csv, verdicts.jsonl, runs/<id>/
    audit/audit_classes.csv                           audited label misses with class and agreement
    downstream/per_item.csv, admitted_attempts.csv, libraries.csv
    cost/calls_tokens.csv, verification_seconds.csv
    Scoring rules from scripts/score_eval.py (round_aware) and scripts/e3_calibrate.py (label_match).

Outputs (under --out, default artifacts/v2/tables)
    t1_rules, t1_rules_mcnemar, t2_audit, t2_audit_2of3_only, t3_check, t3_check_unparsed, t4_k6,
    t5_arms, t5_arms_overlap, t6_downstream, t6_paired, t6_libraries, t7_cost, t7_walltime,
    t8_single_vs_panel, t8_single_vs_panel_errors (each .csv, and one .md per table group),
    t2_audit_list.csv and misses_2of3_only.md. The audit checks are printed on stdout; the
    script exits with status 2 if one of them fails.

Usage (from the repository root)
    python scripts/paper_tables.py [--records artifacts/v2] [--out artifacts/v2/tables]
"""
import argparse
import collections
import csv
import itertools
import json
import math
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from score_eval import round_aware, to_num  # noqa: E402
from e3_calibrate import label_match  # noqa: E402

ap = argparse.ArgumentParser(description="Tables of the paper from artifacts/v2.")
ap.add_argument("--records", default=os.path.join("artifacts", "v2"))
ap.add_argument("--out", default=os.path.join("artifacts", "v2", "tables"))
ARGS = ap.parse_args()
V2, P = ARGS.records, ARGS.out
os.makedirs(P, exist_ok=True)

CAND = {"A": "A-direct", "B": "B-structured", "C": "C-direct"}
FAMNAME = {"A": "A (DeepSeek-V4-Flash)", "B": "B (GPT-6.1 Sol)", "C": "C (Claude Sonnet 5.5)"}
MODELID = {"A": "deepseek-v4-flash", "B": "gpt-6.1-sol", "C": "claude-sonnet-5-5"}
TOL = 1e-4
SETS = ["stream", "confirm", "calibration", "heldout"]
DIR = {"stream": "optmath_295", "confirm": "optmath_200", "calibration": "nanoco_150", "heldout": "nanoco_95"}
RULER = {"stream": "round_aware", "confirm": "round_aware", "calibration": "label_match", "heldout": "label_match"}
SETNAME = {"stream": "stream (OptMATH-295)", "confirm": "confirm (OptMATH-200)",
           "calibration": "calibration (NANO-CO-150)", "heldout": "heldout (NANO-CO-95)"}
FAILED = []


def say(*a):
    print(" ".join(str(x) for x in a))


def jl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]


def jload(p):
    return json.load(open(p, encoding="utf-8"))


def rcsv(p):
    return list(csv.DictReader(open(p, encoding="utf-8", newline="")))


LAB, SRC = {}, {}
for s in SETS:
    rows = rcsv(os.path.join(V2, DIR[s], "problems.csv"))
    LAB[s] = {r["sample_id"]: r["label"] for r in rows}
    SRC[s] = {r["sample_id"]: r["source_record"] for r in rows}


def match(st, value, ruler=None):
    s, sid = st
    lab = LAB[s][sid]
    if value is None:
        return False
    if (ruler or RULER[s]) == "round_aware":
        return bool(round_aware(to_num(value), to_num(lab), lab))
    return bool(label_match(value, lab))


def problems(d):
    return [json.loads(l)["sample_id"] for l in open(os.path.join(V2, d, "verdicts.jsonl"), encoding="utf-8") if l.strip()]


JUDGES = {}
for s in SETS:
    J = collections.defaultdict(dict)
    for r in rcsv(os.path.join(V2, DIR[s], "judges.csv")):
        if r["decision"] == "ACCEPT" and r["clique_value"] != "":
            J[r["rule"]][r["sample_id"]] = float(r["clique_value"])
    JUDGES[s] = J


def judge(s, rule):
    return dict(JUDGES[s][rule])


def full(d, sid, fn="verdict_full.json"):
    p = os.path.join(V2, d, "runs", sid, fn)
    return jload(p) if os.path.isfile(p) else None


def single(s, fam):
    out = {}
    for sid in problems(DIR[s]):
        v = full(DIR[s], sid)
        o = ((v or {}).get("objectives") or {}).get(CAND[fam])
        if isinstance(o, list) and o and o[0] is not None:
            out[sid] = float(o[0])
    return out


def replies(s):
    rep = {f: {} for f in "ABC"}
    for sid in problems(DIR[s]):
        for f in "ABC":
            p = os.path.join(V2, DIR[s], "runs", sid, "verification_%s.json" % f)
            if os.path.isfile(p):
                rep[f][sid] = jload(p)
    return rep


def flags(rep, sid, fl):
    return {f: bool(rep[f].get(sid) and rep[f][sid].get("status") == "ok" and rep[f][sid].get(fl)) for f in "ABC"}


COMBO = {"C": lambda f: f["C"], "A": lambda f: f["A"], "B": lambda f: f["B"], "B or C": lambda f: f["B"] or f["C"],
         "B and C": lambda f: f["B"] and f["C"], "at least two of A, B, C": lambda f: sum(f.values()) >= 2}


def se_p(k, n):
    if not n:
        return None
    p = k / n
    return math.sqrt(p * (1 - p) / n)


def se_mean(xs):
    if len(xs) < 2:
        return None
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) / math.sqrt(len(xs))


def mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n)


def f4(x):
    return "" if x is None else "%.4f" % x


def fp(x):
    return "" if x is None else ("%.4g" % x)


def write(name, header, rows, caption, notes=()):
    with open(os.path.join(P, name + ".csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)
    md = [caption, "", "| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    md += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    if notes:
        md += [""] + list(notes)
    return "\n".join(md) + "\n"


def write_md(name, parts):
    open(os.path.join(P, name + ".md"), "w", encoding="utf-8", newline="\n").write("\n".join(parts))


def cert_row(s, rule, cert, ids):
    c = {sid: v for sid, v in cert.items() if sid in ids}
    n = len(c)
    m = sum(match((s, sid), v) for sid, v in c.items())
    return [SETNAME[s], RULER[s], rule, len(ids), n, f4(n / len(ids)), f4(se_p(n, len(ids))), m, n - m,
            f4(m / n if n else None), f4(se_p(m, n))]


# ---------------------------------------------------------------- Table 1
H1 = ["set", "ruler", "rule", "problems", "certificates", "coverage", "coverage_se", "label_matches", "label_misses",
      "precision", "precision_se"]
rows1, mc_rows, CERTS, REP = [], [], {}, {}
for s in SETS:
    ids = set(problems(DIR[s]))
    rep = REP[s] = replies(s)
    C = {"single_" + f: single(s, f) for f in "ABC"}
    for rule in ("panel_base_2of3", "panel_base_3of3", "gate", "gate_3fam", "gate_tau", "ind_gate", "ind_gate_3fam", "ind_gate_tau"):
        C[rule] = judge(s, rule)
    for base in ("panel_base_3of3", "panel_base_2of3"):
        for cmb in ("B or C", "B and C"):
            C["%s + check (%s)" % (base, cmb)] = {sid: v for sid, v in C[base].items() if not COMBO[cmb](flags(rep, sid, "flag_any"))}
    C = {k: {sid: v for sid, v in c.items() if sid in ids} for k, c in C.items()}
    CERTS[s] = C
    for rule, cert in C.items():
        rows1.append(cert_row(s, rule, cert, ids))
    if RULER[s] == "round_aware":
        a, b3 = C["single_A"], C["panel_base_3of3"]
        both = [sid for sid in sorted(ids) if sid in a and sid in b3]
        ma = {sid: match((s, sid), a[sid]) for sid in both}
        mb = {sid: match((s, sid), b3[sid]) for sid in both}
        x = sum(1 for sid in both if ma[sid] and not mb[sid])
        y = sum(1 for sid in both if mb[sid] and not ma[sid])
        only = [sid for sid in ids if sid in a and sid not in b3]
        mc_rows.append([SETNAME[s], RULER[s], len(both), sum(ma[k] and mb[k] for k in both), x, y,
                        sum(not ma[k] and not mb[k] for k in both), fp(mcnemar(x, y)), len(only),
                        sum(1 for sid in only if not match((s, sid), a[sid]))])
cap1 = ("Table 1. Certification rules. Rulers: OptMATH sets (stream, confirm) `round_aware` of scripts/score_eval.py; "
        "NANO-CO sets (calibration, heldout) `label_match` of scripts/e3_calibrate.py. Stream without the development rows "
        "sample_1..5 (295 problems). Coverage = certificates / problems; an ERROR verdict stays in the denominator and "
        "counts as not certified. Standard errors are binomial, sqrt(p(1-p)/n), n = problems (coverage) or certificates "
        "(precision). single_X: the value of family X's program (A-direct, B-structured, C-direct) at the stated instance "
        "(instance 0) in verdict_full.json (primary sampler), certified when a value is returned. gate rules from the "
        "judge decisions (tau 33.4). `+ check`: the certificate is withdrawn when the named families raise flag_any in "
        "the data verification; an unparsed or missing reply counts as not flagged.")
H1b = ["set", "ruler", "both_certify", "both_match", "single_A_only_match", "panel_base_3of3_only_match", "neither_match",
       "mcnemar_p_two_sided_exact", "certified_by_single_A_not_panel_base_3of3", "of_which_label_misses"]
cap1b = ("Table 1b. single_A against panel_base_3of3 on label match, restricted to the problems that both certify "
         "(ruler `round_aware`; stream without sample_1..5). Exact two-sided McNemar p on the discordant pairs (1 when "
         "there are none). Where both certify, the panel_base_3of3 value is the A-direct value at instance 0 (all three "
         "families agree within 1e-4 relative), so the two values coincide. Last two columns: problems certified by "
         "single_A and not by panel_base_3of3, and their label misses.")
write_md("t1_rules", [write("t1_rules", H1, rows1, cap1), write("t1_rules_mcnemar", H1b, mc_rows, cap1b)])

# ---------------------------------------------------------------- Table 2
AUD = rcsv(os.path.join(V2, "audit", "audit_classes.csv"))
audit = collections.defaultdict(dict)
agree = {}
for r in AUD:
    audit[r["set"]][r["sample_id"]] = r["class"]
    agree[(r["set"], r["sample_id"])] = r["agreement"]
LIST = {s: {sid: c for sid, c in audit[s].items() if not (RULER[s] == "round_aware" and agree[(s, sid)] != "three")} for s in SETS}
with open(os.path.join(P, "t2_audit_list.csv"), "w", encoding="utf-8", newline="\n") as fh:
    fh.write("set,sample_id,class\n")
    for r in AUD:
        if r["sample_id"] in LIST[r["set"]]:
            fh.write("%s,%s,%s\n" % (r["set"], r["sample_id"], r["class"]))
CLS = "DPBTUEM"
miss3 = {}
for s in SETS:
    allids = set(problems(DIR[s]))
    absent = sorted(sid for sid in audit[s] if sid not in allids)
    say("check (a) %s: %d audited ids, %d not in the set %s" % (s, len(audit[s]), len(absent), absent or ""))
    if absent:
        FAILED.append("a " + s)
    c3 = CERTS[s]["panel_base_3of3"]
    miss3[s] = sorted(sid for sid, v in c3.items() if not match((s, sid), v))
    a = set(miss3[s])
    if RULER[s] == "round_aware":
        b = set(LIST[s])
        say("check (b) %s: panel_base_3of3 label misses %d, three-family audited %d, missing from list %s, listed but not a miss %s"
            % (s, len(a), len(b), sorted(a - b) or "none", sorted(b - a) or "none"))
        if a != b:
            FAILED.append("b " + s)
    else:
        say("check (c) %s: panel_base_3of3 label misses %d, not in the audit list: %s" % (s, len(a), sorted(a - set(LIST[s])) or "none"))
        if not a <= set(LIST[s]):
            FAILED.append("c " + s)
H2 = ["set", "ruler", "stage", "certificates", "label_misses"] + ["class_" + c for c in CLS]
rows2 = []
for s in SETS:
    for stage, key in (("panel_base_3of3", "panel_base_3of3"), ("after check (B or C)", "panel_base_3of3 + check (B or C)"),
                       ("after check (B and C)", "panel_base_3of3 + check (B and C)")):
        c = CERTS[s][key]
        ms = [sid for sid, v in c.items() if not match((s, sid), v)]
        cnt = collections.Counter(audit[s][sid] for sid in ms)
        rows2.append([SETNAME[s], RULER[s], stage, len(c), len(ms)] + [cnt.get(k, 0) for k in CLS])
cap2 = ("Table 2. Audit of the panel_base_3of3 label misses by class (classes assigned by re-solving the problems from "
        "their text; artifacts/v2/audit). Rulers: stream and confirm `round_aware`, calibration and heldout `label_match`; "
        "stream without sample_1..5. Classes: D decisive data absent from the problem text; P parameters printed at "
        "truncated precision; B label is not the optimum of the complete text; T text contradicts the instance behind "
        "the label; U text admits two readings; E extraction error; M modeling error shared by the certifying programs.")
H2b = ["set", "ruler", "sample_id", "certified_value_panel_base_2of3", "label"]
rows2b = []
for s in SETS:
    c2 = CERTS[s]["panel_base_2of3"]
    for sid in sorted(c2, key=lambda x: (len(x), x)):
        if not match((s, sid), c2[sid]) and sid not in miss3[s]:
            rows2b.append([SETNAME[s], RULER[s], sid, repr(c2[sid]), LAB[s][sid]])
cap2b = ("Table 2b. Label misses of panel_base_2of3 that are not label misses of panel_base_3of3, per set. Same rulers; "
         "stream without sample_1..5.")
write_md("t2_audit", [write("t2_audit", H2, rows2, cap2), write("t2_audit_2of3_only", H2b, rows2b, cap2b)])

# ---------------------------------------------------------------- Table 3
H3 = ["set", "ruler", "families", "flag", "certificates", "flagged_match", "flagged_miss", "not_flagged_match", "not_flagged_miss"]
rows3, rows3u = [], []
for s in SETS:
    rep = REP[s]
    c3 = CERTS[s]["panel_base_3of3"]
    hit = {sid: match((s, sid), v) for sid, v in c3.items()}
    for cmb in COMBO:
        for fl in ("flag_mismatch", "flag_not_stated", "flag_any"):
            c = [0, 0, 0, 0]
            for sid, h in hit.items():
                c[(0 if COMBO[cmb](flags(rep, sid, fl)) else 2) + (0 if h else 1)] += 1
            rows3.append([SETNAME[s], RULER[s], cmb, fl, len(hit)] + c)
    for fam in ("C", "A", "B"):
        rs = rep[fam]
        rows3u.append([SETNAME[s], fam, MODELID[fam], len(rs), sum(1 for r in rs.values() if r.get("status") != "ok"),
                       sum(1 for sid in c3 if sid in rs and rs[sid].get("status") != "ok"), sum(1 for sid in c3 if sid not in rs)])
cap3 = ("Table 3. Data-verification flags against label match among the panel_base_3of3 certificates. Rulers: stream "
        "and confirm `round_aware`, calibration and heldout `label_match`; stream without sample_1..5. A row with two or "
        "more families counts a problem as flagged when the named combination of family flags holds. Unparsed or "
        "missing replies count as not flagged.")
H3u = ["set", "family", "model", "replies", "unparsed_replies", "unparsed_among_panel_base_3of3_certificates",
       "missing_reply_among_panel_base_3of3_certificates"]
cap3u = ("Table 3b. Unparsed data-verification replies per set and family (status other than ok). Stream without "
         "sample_1..5; on the stream, family B was asked only for the problems that panel_base_2of3 certifies.")
write_md("t3_check", [write("t3_check", H3, rows3, cap3), write("t3_check_unparsed", H3u, rows3u, cap3u)])


# ---------------------------------------------------------------- Table 4
def close(a, b):
    return abs(a - b) <= TOL * max(1.0, abs(a), abs(b))


def stated_rule(v, F):
    obj = v.get("objectives") or {}
    bv = {c: float(x[0]) for c, x in obj.items() if isinstance(x, list) and x and x[0] is not None}
    names = sorted(bv)
    cl = []
    for k in range(len(names), 0, -1):
        for sub in itertools.combinations(names, k):
            if all(close(bv[x], bv[y]) for x, y in itertools.combinations(sub, 2)) and not any(set(sub) <= set(q) for q in cl):
                cl.append(sub)
    q = [c for c in cl if len({x[0] for x in c}) >= F]
    return bv[q[0][0]] if len(q) == 1 else None


def gate_full(v):
    q, inf = v.get("clique") or [], v.get("informative") or []
    if v.get("decision") == "ACCEPT" and q and 0 in inf:
        series = (v.get("objectives") or {}).get(q[0]) or []
        return float(series[0]) if series and series[0] is not None else None
    return None


H4 = ["set", "ruler", "candidates_per_family", "rule", "problems", "certificates", "coverage", "coverage_se",
      "label_matches", "label_misses", "precision", "precision_se"]
rows4, val4 = [], []
RN = (("gate (primary sampler)", gate_full), ("stated instance, two-family agreement", lambda x: stated_rule(x, 2)),
      ("stated instance, three-family agreement", lambda x: stated_rule(x, 3)))
for s, k2 in (("stream", "optmath_295_k2"), ("heldout", "nanoco_95_k2")):
    ids = problems(DIR[s])
    for k, d in ((1, DIR[s]), (2, k2)):
        res = {name: {} for name, _ in RN}
        for sid in ids:
            v = full(d, sid)
            if not v:
                continue
            for name, fn in RN:
                x = fn(v)
                if x is not None:
                    res[name][sid] = x
        for name, cert in res.items():
            r = cert_row(s, name, cert, set(ids))
            rows4.append([r[0], r[1], k, name] + r[3:])
        if k == 1:
            for (name, _), jr in zip(RN, ("gate", "panel_base_2of3", "panel_base_3of3")):
                j = {sid: x for sid, x in judge(s, jr).items() if sid in ids}
                same = set(j) == set(res[name]) and all(abs(j[x] - res[name][x]) < 1e-9 for x in j)
                val4.append("%s, one program per family: %s reproduces the %s decisions (%d certificates): %s" % (s, name, jr, len(j), same))
                if not same:
                    FAILED.append("t4 " + s + " " + jr)
cap4 = ("Table 4. One program per family against two. Rulers: stream `round_aware` (without sample_1..5, 295 problems), "
        "heldout `label_match` (95). gate: the stored primary-sampler verdict (verdict_full.json), ACCEPT with a value at "
        "the stated instance. Stated-instance agreement: all programs' values at instance 0 (three with one program per "
        "family, six with two); programs agree when abs(a-b) <= 1e-4*max(1,|a|,|b|); a clique is a set of pairwise "
        "agreeing programs; certified when exactly one maximal clique spans at least two (or three) families, with that "
        "clique's value. With one program per family these rules are panel_base_2of3 and panel_base_3of3 (validation "
        "below). ERROR verdicts count as not certified.")
write_md("t4_k6", [write("t4_k6", H4, rows4, cap4, ["Validation: " + "; ".join(val4)])])

# ---------------------------------------------------------------- Table 5
ARMS = ["runsok", "vote", "gt", "gate", "gate_tau", "gate_3fam", "panel_base_2of3", "panel_base_3of3", "ind_gate", "ind_gate_tau"]
ATT = rcsv(os.path.join(V2, "downstream", "admitted_attempts.csv"))
tot_ok = sum(int(r["match_host_rule"]) for r in ATT)
tot_ok_ra = sum(int(r["match_round_aware"]) for r in ATT)
adm = {a: {(r["sample_id"], r["attempt"]) for r in ATT if r["admitted_" + a] == "1"} for a in ARMS}
wrong = {a: {(r["sample_id"], r["attempt"]) for r in ATT if r["admitted_" + a] == "1" and r["match_host_rule"] != "1"} for a in ARMS}
wrong_ra = {a: {(r["sample_id"], r["attempt"]) for r in ATT if r["admitted_" + a] == "1" and r["match_round_aware"] != "1"} for a in ARMS}
elig = {a: len({r["sample_id"] for r in ATT if r["admitted_" + a] == "1"}) for a in ARMS}
H5 = ["arm", "admitted", "wrong", "precision", "precision_se", "admitted_correct", "recall", "recall_se", "recall_denominator",
      "eligible_problems", "wrong_round_aware", "precision_round_aware", "admitted_correct_round_aware", "recall_round_aware",
      "recall_denominator_round_aware"]
rows5 = []
for arm in ARMS:
    a, w, wr = len(adm[arm]), len(wrong[arm]), len(wrong_ra[arm])
    rows5.append([arm, a, w, f4((a - w) / a), f4(se_p(a - w, a)), a - w, f4((a - w) / tot_ok), f4(se_p(a - w, tot_ok)), tot_ok,
                  elig[arm], wr, f4((a - wr) / a), a - wr, f4((a - wr) / tot_ok_ra), tot_ok_ra])
cap5 = ("Table 5. Admission of trajectories by arm (rows sample_6..300). A trajectory is an attempt of an eligible row; "
        "admitted when the host's equality rule (label_oracle.host_label: success and equal after rounding to two "
        "decimals half up, else within 0.005) holds against the arm's relabeled answer; wrong when it does not hold "
        "against the vault label. Recall = admitted and correct / all vault-correct trajectories (%d under the host "
        "rule). eligible_problems = problems with at least one admitted attempt. Binomial standard errors. The last five "
        "columns score the same admitted trajectories against the vault label with `round_aware` of "
        "scripts/score_eval.py instead (vault-correct trajectories: %d)." % (tot_ok, tot_ok_ra))
O5 = ["panel_base_3of3", "panel_base_2of3", "vote", "runsok", "gt"]
H5b = ["arm_a", "arm_b", "shared", "a_only", "b_only", "shared_wrong", "a_only_wrong", "b_only_wrong"]
rows5b = [[x, y, len(adm[x] & adm[y]), len(adm[x] - adm[y]), len(adm[y] - adm[x]), len(wrong[x] & wrong[y]),
           len(wrong[x] - adm[y]), len(wrong[y] - adm[x])] for x, y in itertools.combinations(O5, 2)]
cap5b = ("Table 5b. Pairwise overlap of admitted trajectories (identified by problem and attempt position), rows "
         "sample_6..300; wrong under the host rule against the vault label. a_only_wrong = wrong trajectories of arm a "
         "that arm b does not admit.")
write_md("t5_arms", [write("t5_arms", H5, rows5, cap5), write("t5_arms_overlap", H5b, rows5b, cap5b)])

# ---------------------------------------------------------------- Table 6
B = [("complexor", "ComplexOR", 18), ("industryor", "IndustryOR", 100), ("mamo_c", "Mamo.Complex", 211),
     ("optmath", "OptMATH-Bench", 166), ("optibench", "OptiBench", 605)]
CFG = ["panel_base_3of3", "panel_base_2of3", "vote", "runsok", "gt", "nolib", "released"]
CNAME = {"nolib": "host without learned library",
         "released": "released library (host); build data as described in the host README, no build record"}
HH = collections.defaultdict(dict)
for r in rcsv(os.path.join(V2, "downstream", "per_item.csv")):
    HH[(r["configuration"], r["pass"], r["benchmark"])][r["item_id"]] = r["match_round_aware"] == "1"
HH = {k: v for k, v in HH.items() if len(v) == dict((b, n) for b, _, n in B)[k[2]]}
H6 = ["configuration", "benchmark", "n", "passes", "solved_r1", "solved_r2", "solved_r3", "acc_r1", "acc_r2", "acc_r3", "mean", "se_mean"]
rows6 = []


def pad(xs, fmt):
    return [fmt % xs[i] if i < len(xs) else "" for i in range(3)]


for lib in CFG:
    passes = [ps for ps in ("r1", "r2", "r3") if all((lib, ps, b) in HH for b, _, _ in B)]
    for b, bn, n in B:
        k = [sum(HH[(lib, ps, b)].values()) for ps in passes]
        acc = [100.0 * x / n for x in k]
        rows6.append([CNAME.get(lib, lib), bn, n, len(passes)] + pad(k, "%d") + pad(acc, "%.2f") +
                     ["%.2f" % (sum(acc) / len(acc)), ("%.2f" % se_mean(acc)) if len(acc) > 1 else ""])
    k = [sum(sum(HH[(lib, ps, b)].values()) for b, _, _ in B) for ps in passes]
    acc = [100.0 * x / 1100 for x in k]
    rows6.append([CNAME.get(lib, lib), "micro-average", 1100, len(passes)] + pad(k, "%d") + pad(acc, "%.2f") +
                 ["%.2f" % (sum(acc) / len(acc)), ("%.2f" % se_mean(acc)) if len(acc) > 1 else ""])
    mac = [sum(100.0 * sum(HH[(lib, ps, b)].values()) / n for b, _, n in B) / 5 for ps in passes]
    rows6.append([CNAME.get(lib, lib), "macro-average (mean of the five benchmarks)", "", len(passes), "", "", ""] + pad(mac, "%.2f") +
                 ["%.2f" % (sum(mac) / len(mac)), ("%.2f" % se_mean(mac)) if len(mac) > 1 else ""])
cap6 = ("Table 6. Downstream accuracy, `round_aware` of scripts/score_eval.py on the 1,100 evaluation items (unparseable "
        "predictions count as wrong); per pass, mean over the passes and standard error of the mean (n-1 in the "
        "variance); micro-average over the 1,100 items, macro-average = mean of the five benchmark accuracies. "
        "Accuracies in percent.")
notes6 = ["Host without learned library: `main.py --phase cluster` (learning-phase solve path) with `--top-k 1` on blind "
          "copies of the benchmarks, process ended before any library build; prediction = the solver agent's "
          "final_result, else the result of the first successful attempt. Its two differences from the evaluation "
          "path besides the absent skill: (1) the keyword extractor has no library keyword reference; (2) a backend "
          "selector replaces the skill selector.",
          "Released library (host); build data as described in the host README, no build record: pass r1 with the "
          "evaluation command of the other passes and `--source-skill-library` = the host's "
          "`skill_library/skill_library_learned`; its build data is taken from the host README (clustering on the "
          "first 150 problems of optmath-train-300.jsonl, learning phase on the other 150), for which no build record "
          "exists."]


def view(lib, mode, b):
    if mode == "r1":
        return HH.get((lib, "r1", b))
    vs = [HH.get((lib, ps, b)) for ps in ("r1", "r2", "r3")]
    if any(v is None for v in vs):
        return None
    return {k: sum(v[k] for v in vs) >= 2 for k in vs[0]}


def paired(x, mx, y, my, mode, out):
    vx = [view(x, mx, b) for b, _, _ in B]
    vy = [view(y, my, b) for b, _, _ in B]
    if any(v is None for v in vx + vy):
        return
    tot = [0, 0, 0, 0]
    for (b, bn, n), hx, hy in zip(B, vx, vy):
        c = [sum(hx[k] and hy[k] for k in hx), sum(hx[k] and not hy[k] for k in hx), sum(hy[k] and not hx[k] for k in hx),
             sum(not hx[k] and not hy[k] for k in hx)]
        tot = [a + b2 for a, b2 in zip(tot, c)]
        out.append([CNAME.get(x, x), CNAME.get(y, y), mode, bn, n] + c + [fp(mcnemar(c[1], c[2]))])
    out.append([CNAME.get(x, x), CNAME.get(y, y), mode, "all 1,100", 1100] + tot + [fp(mcnemar(tot[1], tot[2]))])


H6b = ["first", "second", "passes", "benchmark", "n", "both", "only_first", "only_second", "neither", "mcnemar_p"]
rows6b = []
for mode, m in (("r1", "r1"), ("majority of r1-r3", "maj")):
    for x, y in itertools.combinations(CFG, 2):
        paired(x, m, y, m, mode, rows6b)
paired("released", "r1", "nolib", "maj", "released r1 against majority of r1-r3", rows6b)
cap6b = ("Table 6b. Paired comparisons (`round_aware`; solved = round-aware hit). r1: pass r1 of each configuration; "
         "majority: per item solved in at least two of r1 to r3, only where both have three passes; one mixed row set "
         "compares released r1 with the majority of r1 to r3 of the host without learned library. Exact two-sided "
         "McNemar p on the discordant items.")
LIBS = {r["configuration"]: r for r in rcsv(os.path.join(V2, "downstream", "libraries.csv"))}
H6c = ["configuration", "library_files", "admitted_trajectories", "wrong_trajectories", "wrong_share", "wrong_share_se"]
rows6c = []
for lib in CFG:
    if lib == "nolib":
        rows6c.append([CNAME[lib], 0, "", "", "", ""])
    elif lib == "released":
        rows6c.append([CNAME[lib], LIBS[lib]["library_files"], "", "", "", ""])
    else:
        a, w = len(adm[lib]), len(wrong[lib])
        rows6c.append([lib, LIBS[lib]["library_files"], a, w, f4(w / a), f4(se_p(w, a))])
cap6c = ("Table 6c. Library size (files in the built library folder) and the share of wrong trajectories among those "
         "admitted (Table 5, host rule against the vault label, rows sample_6..300).")
write_md("t6_downstream", [write("t6_downstream", H6, rows6, cap6, notes6), write("t6_paired", H6b, rows6b, cap6b),
                           write("t6_libraries", H6c, rows6c, cap6c)])

# ---------------------------------------------------------------- Table 7
COST = rcsv(os.path.join(V2, "cost", "calls_tokens.csv"))
CN = {"optmath_295": "stream", "optmath_200": "confirm", "nanoco_150": "calibration", "nanoco_95": "heldout",
      "optmath_295_k2": "stream, two programs per family", "nanoco_95_k2": "heldout, two programs per family"}
H7 = ["set", "stage", "family", "role", "calls", "prompt_tokens", "completion_tokens", "reasoning_tokens", "problems",
      "calls_per_problem", "prompt_tokens_per_problem", "completion_tokens_per_problem"]
rows7 = []
for stage in ("certification", "data verification"):
    for d in CN:
        rs = [r for r in COST if r["set"] == d and r["stage"] == stage]
        if not rs:
            continue
        tot = [0, 0, 0, 0]
        n = int(rs[0]["problems"])
        for r in rs:
            t = [int(r[k]) for k in ("calls", "prompt_tokens", "completion_tokens", "reasoning_tokens")]
            tot = [a + b for a, b in zip(tot, t)]
            rows7.append([CN[d], stage, r["family"], r["role"]] + t + [n, "%.2f" % (t[0] / n), "%.0f" % (t[1] / n), "%.0f" % (t[2] / n)])
        rows7.append([CN[d], stage, "all", "all"] + tot + [n, "%.2f" % (tot[0] / n), "%.0f" % (tot[1] / n), "%.0f" % (tot[2] / n)])
cap7 = ("Table 7. Model calls and tokens by family and role. Certification: usage records of the certification runs "
        "(role extractor = the family A call with max_tokens 8192, generation = every other call; the records carry no "
        "problem id, so the stream certification rows cover all 300 problems including sample_1..5 and per-problem "
        "means divide by the problems of the set, ERROR verdicts included; the rows with two programs per family include "
        "the reruns of problems whose first attempt ended in an API error). Data verification: one request per problem "
        "and family (stream without sample_1..5; family B on the stream only for the problems that panel_base_2of3 "
        "certifies); per-problem means divide by the problems with a request. No prices.")
H7w = ["set", "stage", "problems", "median_seconds", "min_seconds", "max_seconds"]
rows7w = []
for d in CN:
    el = [json.loads(l).get("elapsed_s") for l in open(os.path.join(V2, d, "verdicts.jsonl"), encoding="utf-8") if l.strip()]
    el = [x for x in el if isinstance(x, (int, float))]
    rows7w.append([CN[d], "certification", len(el), "%.1f" % statistics.median(el), "%.1f" % min(el), "%.1f" % max(el)])
VS = rcsv(os.path.join(V2, "cost", "verification_seconds.csv"))
for d in ("optmath_295", "optmath_200", "nanoco_150", "nanoco_95"):
    v = [float(r["request_seconds_summed"]) for r in VS if r["set"] == d]
    rows7w.append([CN[d], "data verification (request seconds summed over the families of a problem)", len(v),
                   "%.1f" % statistics.median(v), "%.1f" % min(v), "%.1f" % max(v)])
cap7w = ("Table 7b. Wall time per problem. Certification: elapsed_s of the stored verdicts (stream without sample_1..5); "
         "the problems of a set ran in parallel, so the sum exceeds the elapsed wall time of the set.")
write_md("t7_cost", [write("t7_cost", H7, rows7, cap7), write("t7_walltime", H7w, rows7w, cap7w)])

# ---------------------------------------------------------------- Table 8
GROUPS = ["(i) audited, class D/P/B/T/U (benchmark side)", "(ii) audited, class E/M (pipeline side)",
          "(iii) not audited, panel_base_3of3 certifies a matching value", "(iv) all other problems"]
H8 = ["set", "ruler", "rule", "group", "problems_in_group", "certificates", "label_matches", "label_misses"]
rows8, rows8b = [], []
for s in ("stream", "confirm"):
    ids = problems(DIR[s])
    C = CERTS[s]
    c3 = C["panel_base_3of3"]
    aud = LIST[s]
    rules = {k: C[k] for k in ("single_A", "single_B", "single_C", "panel_base_2of3", "panel_base_3of3", "panel_base_3of3 + check (B or C)")}

    def group(sid):
        if sid in aud:
            return 0 if aud[sid] in "DPBTU" else 1
        if sid in c3 and match((s, sid), c3[sid]):
            return 2
        return 3
    gmap = {sid: group(sid) for sid in ids}
    gsize = [sum(1 for g in gmap.values() if g == k) for k in range(4)]
    for rule, cert in rules.items():
        tot = [0, 0, 0]
        for k in range(4):
            cs = [sid for sid in cert if gmap[sid] == k]
            m = sum(match((s, sid), cert[sid]) for sid in cs)
            rows8.append([SETNAME[s], "round_aware", rule, GROUPS[k], gsize[k], len(cs), m, len(cs) - m])
            tot = [tot[0] + len(cs), tot[1] + m, tot[2] + len(cs) - m]
        rows8.append([SETNAME[s], "round_aware", rule, "all groups", len(ids)] + tot)
    for rule in ("single_A", "single_B", "single_C", "panel_base_2of3"):
        cert = rules[rule]
        g3 = [x for x in ids if gmap[x] == 2]
        g4 = [x for x in ids if gmap[x] == 3]
        rows8b.append([SETNAME[s], "round_aware", rule, len(g3), sum(1 for x in g3 if x in cert),
                       sum(1 for x in g3 if x in cert and not match((s, x), cert[x])), len(g4), sum(1 for x in g4 if x in cert),
                       sum(1 for x in g4 if x in cert and not match((s, x), cert[x]))])
cap8 = ("Table 8. Single families against the panel, split by audit group. Ruler `round_aware` of scripts/score_eval.py; "
        "stream without sample_1..5 (295 problems), confirm 200 problems (ERROR verdicts count as not certified). Groups, "
        "from the three-family audit list only: (i) audited, class D, P, B, T or U (benchmark side); (ii) audited, class E "
        "or M (pipeline side); (iii) not audited, and panel_base_3of3 certifies a value that matches the label; (iv) every "
        "other problem. single_X certifies the value of family X's program at the stated instance (instance 0 of "
        "verdict_full.json) whenever one is returned. `+ check (B or C)` withdraws the certificate when family B or C "
        "raises flag_any in the data verification; unparsed or missing replies count as not flagged.")
H8b = ["set", "ruler", "rule", "group_iii_problems", "group_iii_value_returned", "group_iii_label_misses",
       "group_iv_problems", "group_iv_value_returned", "group_iv_label_misses"]
cap8b = ("Table 8b. Errors of each single family and of panel_base_2of3 on group (iii) (problems whose label "
         "panel_base_3of3 confirms) and on group (iv). value_returned = problems of the group the rule certifies; "
         "label_misses = those whose value misses the label under `round_aware`.")
write_md("t8_single_vs_panel", [write("t8_single_vs_panel", H8, rows8, cap8), write("t8_single_vs_panel_errors", H8b, rows8b, cap8b)])

# ---------------------------------------------------------------- two-family-only misses export
LIST_RULES = ("gate", "gate_3fam", "gate_tau", "panel_base_2of3", "panel_base_3of3", "ind_gate", "ind_gate_tau")
PROGS = ("A-direct", "B-structured", "C-direct")


def fence(t, lang=""):
    n = 3
    while "`" * n in t:
        n += 1
    return "`" * n + lang + "\n" + t.rstrip("\n") + "\n" + "`" * n


def fmt(x):
    if isinstance(x, float) and x.is_integer():
        return str(x)
    return repr(x) if x is not None else "none"


QUESTION = {s: {json.loads(l)["sample_id"]: json.loads(l)["question"] for l in open(os.path.join(V2, DIR[s], "workorder.jsonl"), encoding="utf-8")}
            for s in ("stream", "confirm")}


def section(k, s, sid):
    rd = os.path.join(V2, DIR[s], "runs", sid)
    q = QUESTION[s][sid]
    acc = {r: JUDGES[s][r][sid] for r in LIST_RULES if sid in JUDGES[s][r]}
    mn, mx = bool(re.search(r"\bminim", q, re.I)), bool(re.search(r"\bmaxim", q, re.I))
    sense = "min" if mn and not mx else "max" if mx and not mn else "not determined from the problem text"
    vals = {}
    for r, v in acc.items():
        vals.setdefault(fmt(v), []).append(r)
    val = next(iter(vals)) if len(vals) == 1 else "; ".join("%s (%s)" % (x, ", ".join(rs)) for x, rs in vals.items())
    rules = ", ".join(r for r in LIST_RULES if r in acc)
    src = "`artifacts/v2/%s/problems.csv`, OptMATH-Train record %s, field `answer`; the dataset stores no solution" % (DIR[s], SRC[s][sid])
    v = jload(os.path.join(rd, "verdict_full.json"))
    ob, st = v.get("objectives") or {}, v.get("statuses") or {}
    v0 = {f: (float(ob[c][0]) if isinstance(ob.get(c), list) and ob[c] and ob[c][0] is not None else None) for f, c in CAND.items()}
    s0 = {f: (st.get(c) or [None])[0] for f, c in CAND.items()}
    have = [f for f in "ABC" if v0[f] is not None]
    pairs = [(x, y) for x, y in itertools.combinations(have, 2) if close(v0[x], v0[y])]
    clique = ", ".join("%s and %s" % (FAMNAME[x], FAMNAME[y]) for x, y in pairs)
    third = ", ".join("%s returns %s" % (FAMNAME[f], fmt(v0[f])) for f in "ABC" if not any(f in pr for pr in pairs)) or "none"
    o = ["## %d. %s (%s)" % (k, sid, SETNAME[s]), "", "### 1. Identification", "", "| Field | Value |", "|---|---|",
         "| Sample id | `%s` |" % sid, "| Set | %s |" % SETNAME[s], "| Source record | OptMATH-Train record %s |" % SRC[s][sid],
         "| Optimization sense | %s (words \"minim...\" / \"maxim...\" in the problem text) |" % sense,
         "| Certified value (panel_base_2of3) | %s |" % fmt(acc["panel_base_2of3"]), "| Label | %s |" % LAB[s][sid],
         "| Rules that certify it | %s (values: %s) |" % (rules, val), "| Label source | %s |" % src, "",
         "### 2. Certifying clique of panel_base_2of3 and values at instance 0", "",
         "Families that agree at the stated instance (abs(a-b) <= 1e-4*max(1,|a|,|b|)): %s. The third family: %s." % (clique, third),
         "", "| Family | Program | Value at instance 0 | Status at instance 0 | In the certifying clique | Matches the label (round_aware) |",
         "|---|---|---|---|---|---|"]
    for f in "ABC":
        stx = str(s0[f]).replace("|", "\\|").replace("\r", " ").replace("\n", " ")
        o.append("| %s | %s.py | %s | %s | %s | %s |" % (FAMNAME[f], CAND[f], fmt(v0[f]), stx, "yes" if any(f in pr for pr in pairs) else "no",
                                                        "yes" if match((s, sid), v0[f]) else "no"))
    o += ["", "### 3. Problem text", "", fence(q), ""]
    sp = jload(os.path.join(rd, "spec.json"))
    lines = ["\"%s\": %s" % (n, json.dumps(x, ensure_ascii=False, separators=(",", ":"))) for n, x in (sp.get("spec") or {}).items()]
    o += ["### 4. spec.json (`spec` and `warnings`)", "", fence("\n".join(lines), "json"), "", "Warnings:", "",
          fence("\n".join(sp.get("warnings") or []) or "none"), "", "### 5. Programs", ""]
    for p in PROGS:
        pp = os.path.join(rd, p + ".py")
        o += ["#### %s.py" % p, "", fence(open(pp, encoding="utf-8").read() if os.path.isfile(pp) else "(no program file)", "python"), ""]
    o += ["### 6. Objective values", "", "Rules that certify it: %s." % rules, ""]
    for name, fn in (("param_screen", "verdict_full.json"), ("independent", "verdict_independent.json")):
        vv = jload(os.path.join(rd, fn))
        ob, st = vv.get("objectives") or {}, vv.get("statuses") or {}
        n = max((len(x) for x in ob.values()), default=0)
        o += ["#### %s" % name, "", "Decision: %s; clique %s; informative instances %s. Instance 0 is the stated instance." % (
            vv["decision"], ", ".join(vv.get("clique") or []) or "none", vv.get("informative")), "",
              "| Instance | " + " | ".join(PROGS) + " |", "|---|" + "---|" * len(PROGS)]
        for i in range(n):
            cells = []
            for p in PROGS:
                a, sts = ob.get(p, []), st.get(p, [])
                stx = str(sts[i] if i < len(sts) else None).replace("|", "\\|").replace("\r", " ").replace("\n", " ")
                cells.append("%s (%s)" % (fmt(a[i]) if i < len(a) else "none", stx))
            o.append("| %s | " % ("0 (stated)" if i == 0 else str(i)) + " | ".join(cells) + " |")
        o.append("")
    return "\n".join(o) + "\n", (sid, SETNAME[s], fmt(acc["panel_base_2of3"]), LAB[s][sid], rules, clique)


secs = [section(k, s, sid) for k, (s, sid) in enumerate([(s, r[2]) for s in ("stream", "confirm") for r in rows2b if r[0] == SETNAME[s]], 1)]
head = ["# panel_base_2of3 label misses that are not panel_base_3of3 label misses", "",
        "Included: the problems of Table 2b on the OptMATH sets, ruler `round_aware` (scripts/score_eval.py): "
        "panel_base_2of3 certifies them with a value that differs from the label and panel_base_3of3 does not certify "
        "them. Section 2 gives the families of the certifying clique and the value each family returns at instance 0. "
        "Problem text is the `question` field given to the models; objective values are from `verdict_full.json` "
        "(param_screen) and `verdict_independent.json` (independent). Classes are in artifacts/v2/audit.", "",
        "| Sample id | Set | panel_base_2of3 value | Label | Rules that certify it | Certifying clique (families agreeing at instance 0) |",
        "|---|---|---|---|---|---|"]
for _, (sid, sn, v, lab, rules, clique) in secs:
    head.append("| `%s` | %s | %s | %s | %s | %s |" % (sid, sn, v, lab, rules, clique))
open(os.path.join(P, "misses_2of3_only.md"), "w", encoding="utf-8", newline="\n").write("\n".join(head) + "\n\n" + "\n".join(t for t, _ in secs))
for l in val4:
    say(l)
say("tables written to", P)
if FAILED:
    say("CHECK FAILED:", FAILED)
    sys.exit(2)
