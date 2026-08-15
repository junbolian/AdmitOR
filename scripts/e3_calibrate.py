"""AdmitOR E3 -- e3_calibrate.py (v0.1)

Conformal calibration of the admission gate on the NANO-CO instance set,
then a zero-token replay onto the 300 E1 certification verdicts.

The calibration route uses the solver-verified NANO-CO instances as
labeled calibration problems: the gate certifies a stratified sample of
them exactly as it certified the mining stream, and because every
NANO-CO answer is solver-verified by construction, each ACCEPT verdict
self-labels as a TRUE clique (certified value matches the verified
answer) or a FALSE clique (it does not). The false-clique scores form
the null population that Lemma B's FDR p-values require; no benchmark
labels are touched.

Three stages, run in order:

  1) workorder  -- emit a gate work order from nano-co.jsonl (no tokens)
       python scripts/e3_calibrate.py workorder \
           --nano <OptSkills>/datasets/train_set/nano-co.jsonl \
           --out outputs/e3/e3_workorder.jsonl \
           --labels outputs/e3/e3_labels.jsonl --n 150 --seed 42
     then certify it with the UNCHANGED e1_certify.py (this step costs
     tokens):
       python scripts/e1_certify.py --work-order outputs/e3/e3_workorder.jsonl \
           --verdicts-dir outputs/e3/verdicts --runs-dir outputs/e3/certify_runs

  2) fit        -- label calibration verdicts, fit the conformal threshold
       python scripts/e3_calibrate.py fit --runs outputs/e3/certify_runs \
           --labels outputs/e3/e3_labels.jsonl --alpha 0.05 \
           --out outputs/e3/calibration.json
     (fit reads the rich <sid>/verdict_full.json artifacts; the compact
      files under --verdicts-dir are GateOracle-format and carry no
      clique geometry)

  3) replay     -- apply the calibrated rule to the 300 E1 verdicts (no tokens)
       python scripts/e3_calibrate.py replay \
           --calibration outputs/e3/calibration.json \
           --e1-runs artifacts/e1/certify_runs \
           --verdicts artifacts/e1/certify_verdicts \
           --workorder outputs/e1/gate_workorder.jsonl \
           --vault <path to vault labels jsonl> \
           --out outputs/e3/e3_report.json

Score (preregistered here, identical for calibration and replay):
    s = 10 * families_spanned_by_clique + clique_size + informative_count / 10
computed from verdict fields only; family of a member is its leading
letter (A/B/C). Selection = the smallest score threshold tau whose selected calibration
set carries a binomial false-discovery certificate (point false rate
<= alpha and Clopper-Pearson 95% upper bound <= 2*alpha, mirroring K3);
BH-on-conformal-p is recovered as the null sample grows, but the exact
binomial certificate is honest at pilot sample sizes. Non-ACCEPT
verdicts are never admitted, and the replayed FDR on E1 is measured
out-of-sample against the sealed vault.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import random
from typing import Any, Dict, List

# ---------------------------------------------------------------- shared ----


def norm_question(text: str) -> str:
    return " ".join(str(text).split())


def question_hash(text: str) -> str:
    return hashlib.sha256(norm_question(text).encode("utf-8")).hexdigest()[:16]


def to_num(x):
    if x is None:
        return None
    if isinstance(x, (int, float)):
        return float(x)
    s = str(x).strip().replace(",", "").rstrip("%")
    try:
        return float(s)
    except ValueError:
        return None


def dec_places(x):
    s = str(x).strip()
    return len(s.split(".")[1]) if "." in s else 0


def rel_match_ra(pred, ans, rel):
    if pred is None or ans is None:
        return False
    return abs(pred - ans) <= max(1e-9, rel * abs(ans))


def round_aware(pred, ans_num, ans_raw):
    """The paper's uniform scorer tier (score_eval.py, verbatim logic)."""
    if pred is None or ans_num is None:
        return False
    if rel_match_ra(pred, ans_num, 1e-4):
        return True
    try:
        return round(pred, dec_places(ans_raw)) == ans_num
    except Exception:
        return False


def label_match(certified: Any, answer: Any) -> bool:
    """Same ruler as the GT oracle: 2dp half-up string match, abs-gap fallback."""
    try:
        c = float(certified)
        a = float(str(answer).strip())
    except (TypeError, ValueError):
        return False
    from decimal import ROUND_HALF_UP, Decimal

    q = Decimal("0.01")
    try:
        if Decimal(repr(c)).quantize(q, rounding=ROUND_HALF_UP) == Decimal(repr(a)).quantize(
            q, rounding=ROUND_HALF_UP
        ):
            return True
    except Exception:
        pass
    return abs(c - a) <= 0.005


def verdict_score(v: Dict[str, Any]) -> float:
    clique = v.get("clique") or []
    families = {str(m)[:1] for m in clique}
    informative = v.get("informative") or []
    return 10.0 * len(families) + len(clique) + len(informative) / 10.0


def certified_value(v: Dict[str, Any]) -> Any:
    obj = v.get("objectives") or {}
    clique = v.get("clique") or []
    if not clique:
        return None
    vals = obj.get(clique[0]) or []
    return vals[0] if vals else None


def load_verdicts(vdir: str) -> Dict[str, Dict[str, Any]]:
    out = {}
    for name in sorted(os.listdir(vdir)):
        if name.endswith(".json"):
            with open(os.path.join(vdir, name), encoding="utf-8") as f:
                out[name[:-5]] = json.load(f)
    return out


# ------------------------------------------------------------- workorder ----


def cmd_workorder(a: argparse.Namespace) -> None:
    rows = [json.loads(l) for l in open(a.nano, encoding="utf-8") if l.strip()]
    rng = random.Random(a.seed)
    by_type: Dict[str, List[Dict[str, Any]]] = {}
    for r in rows:
        by_type.setdefault(str(r.get("problem_type", "?")), []).append(r)
    for v in by_type.values():
        rng.shuffle(v)
    picked: List[Dict[str, Any]] = []
    idx = 0
    while len(picked) < min(a.n, len(rows)):
        for t in sorted(by_type):
            if idx < len(by_type[t]) and len(picked) < a.n:
                picked.append(by_type[t][idx])
        idx += 1
        if idx > max(len(v) for v in by_type.values()):
            break
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as wo, open(a.labels, "w", encoding="utf-8") as lb:
        for i, r in enumerate(picked, 1):
            sid = f"e3_{r.get('problem_type','x')}_{r.get('index', i)}"
            q = r["question"]
            wo.write(json.dumps({"sample_id": sid, "question": q}, ensure_ascii=False) + "\n")
            lb.write(
                json.dumps(
                    {
                        "sample_id": sid,
                        "question": q,
                        "answer": r.get("answer"),
                        "problem_type": r.get("problem_type"),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    print(f"[workorder] {len(picked)} problems -> {a.out}; labels -> {a.labels}")
    print(
        "[workorder] next: run e1_certify.py on this work order "
        "(same env vars as the E1 certification night)"
    )


# ------------------------------------------------------------------- fit ----


def load_rich_verdicts(runs_dir: str) -> Dict[str, Dict[str, Any]]:
    out = {}
    for sid in sorted(os.listdir(runs_dir)):
        vf = os.path.join(runs_dir, sid, "verdict_full.json")
        if os.path.isfile(vf):
            with open(vf, encoding="utf-8") as f:
                out[sid] = json.load(f)
    return out


def cmd_fit(a: argparse.Namespace) -> None:
    labels = {
        json.loads(l)["sample_id"]: json.loads(l)
        for l in open(a.labels, encoding="utf-8")
        if l.strip()
    }
    verdicts = load_rich_verdicts(a.runs)
    if not verdicts:
        raise SystemExit(
            f"[fit] no <sid>/verdict_full.json under {a.runs} -- "
            "point --runs at the certify runs dir"
        )
    pos, null, skipped = [], [], 0
    for sid, v in verdicts.items():
        if sid not in labels:
            continue
        if v.get("decision") != "ACCEPT":
            skipped += 1
            continue
        s = verdict_score(v)
        ok = label_match(certified_value(v), labels[sid]["answer"])
        (pos if ok else null).append({"sample_id": sid, "score": s})
    if len(null) < 3:
        print(
            f"[fit] WARNING: only {len(null)} false-clique records -- "
            "conformal p-values will be coarse; consider raising --n in "
            "the workorder stage"
        )
    # threshold selection: smallest tau whose selected set carries a
    # binomial false-discovery certificate (point <= alpha, CP95 <= 2*alpha,
    # mirroring K3's point/upper criteria); maximizes coverage subject to it.
    allrec = [(r["score"], 0) for r in pos] + [(r["score"], 1) for r in null]
    taus = sorted({s for s, _ in allrec})
    table = []
    chosen = None
    for t in taus:
        sel = [(s, bad) for s, bad in allrec if s >= t]
        nb = sum(bad for _, bad in sel)
        row = {
            "tau": t,
            "selected": len(sel),
            "false_selected": nb,
            "false_rate": nb / len(sel) if sel else None,
            "cp95_upper": clopper_pearson_upper(nb, len(sel)) if sel else None,
        }
        table.append(row)
        if (
            sel
            and row["false_rate"] <= a.alpha
            and row["cp95_upper"] <= 2 * a.alpha
            and chosen is None
        ):
            chosen = t
    report = {
        "alpha": a.alpha,
        "n_accept": len(pos) + len(null),
        "n_true_clique": len(pos),
        "n_false_clique": len(null),
        "null_scores": sorted(r["score"] for r in null),
        "positive_scores": sorted(r["score"] for r in pos),
        "raw_false_rate_on_calibration": (
            (len(null) / (len(pos) + len(null))) if (pos or null) else None
        ),
        "tau": chosen,
        "threshold_table": table,
        "records": {"positive": pos, "null": null},
    }
    if chosen is None:
        print(
            "[fit] WARNING: no threshold met the certificate on "
            "calibration; replay will refuse until --n is raised"
        )
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(
        f"[fit] ACCEPTs {report['n_accept']}: true {len(pos)} / false "
        f"{len(null)}; raw false rate "
        f"{report['raw_false_rate_on_calibration']}; -> {a.out}"
    )


# ---------------------------------------------------------------- replay ----


def conformal_pvalue(score: float, null_scores: List[float]) -> float:
    n = len(null_scores)
    ge = sum(1 for s in null_scores if s >= score)
    return (1.0 + ge) / (n + 1.0)


def bh_accept(pvals: List[float], alpha: float) -> List[bool]:
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    k = 0
    m = len(pvals)
    for rank, i in enumerate(order, 1):
        if pvals[i] <= alpha * rank / m:
            k = rank
    cut = set(order[:k])
    return [i in cut for i in range(m)]


def clopper_pearson_upper(x: int, n: int, conf: float = 0.95) -> float:
    if n == 0:
        return 1.0
    lo, hi = 0.0, 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        # P[Bin(n, mid) <= x] via regularized incomplete beta complement
        cdf = sum(math.comb(n, k) * mid**k * (1 - mid) ** (n - k) for k in range(0, x + 1))
        if cdf > 1 - conf:
            lo = mid
        else:
            hi = mid
    return hi


def cmd_replay(a: argparse.Namespace) -> None:
    cal = json.load(open(a.calibration, encoding="utf-8"))
    tau = cal.get("tau")
    if tau is None:
        raise SystemExit(
            "[replay] calibration carries no certified tau -- "
            "raise the workorder --n and refit before replaying"
        )
    alpha = cal["alpha"]
    sid_to_q = {}
    for l in open(a.workorder, encoding="utf-8"):
        if l.strip():
            rec = json.loads(l)
            sid_to_q[str(rec.get("sample_id"))] = rec.get("question", "")
    # vault join: auto-detect the file's shape. Question-bearing files
    # join by question hash; index-bearing label files (the sealed vault
    # stores answers keyed by mining index, questions live in the blind
    # file) join directly by sample_id.
    vault_rows = [json.loads(l) for l in open(a.vault, encoding="utf-8") if l.strip()]
    if not vault_rows:
        raise SystemExit("[replay] vault file is empty")
    vault = {}
    vault_by_sid = {}
    if "question" in vault_rows[0]:
        join_mode = "question-hash"
        for rec in vault_rows:
            vault[question_hash(rec["question"])] = rec.get("answer")
    else:
        idx_key = next((k for k in ("index", "idx", "source_index") if k in vault_rows[0]), None)
        if idx_key is None:
            raise SystemExit(
                f"[replay] vault rows carry neither question "
                f"nor index; keys = {list(vault_rows[0])}"
            )
        join_mode = f"sample_id via {idx_key}"
        for rec in vault_rows:
            vault_by_sid[f"sample_{rec[idx_key]}"] = rec.get("answer")
    print(f"[replay] vault: {len(vault_rows)} labels, join mode: {join_mode}")
    excluded = {s.strip() for s in a.exclude.split(",") if s.strip()}
    rows = []
    accepts_total = 0
    accepts_no_value = 0
    for name in sorted(os.listdir(a.verdicts)):
        if not name.endswith(".json"):
            continue
        sid = name[:-5]
        if sid in excluded:
            continue
        compact = json.load(open(os.path.join(a.verdicts, name), encoding="utf-8"))
        if compact.get("decision") != "ACCEPT":
            continue
        accepts_total += 1
        cval = compact.get("clique_value")
        if cval is None:
            # an ACCEPT without a base-instance value admits nothing in E1
            # (GateOracle routes it to NO_CONSENSUS); it cannot be a false
            # discovery and is excluded from the admitted set here too
            accepts_no_value += 1
            continue
        vf = os.path.join(a.e1_runs, sid, "verdict_full.json")
        if not os.path.isfile(vf):
            continue
        v = json.load(open(vf, encoding="utf-8"))
        q = v.get("question") or sid_to_q.get(sid, "")
        h = question_hash(q) if q else None
        rows.append(
            {
                "sample_id": sid,
                "score": verdict_score(v),
                "certified": cval,
                "qhash": h,
                "informative": len(v.get("informative") or []),
            }
        )
    if not rows:
        raise SystemExit("[replay] no value-bearing ACCEPT verdicts found")
    if a.tau is not None:
        tau = a.tau
    admitted = [r for r in rows if r["score"] >= tau]
    missing_q = sum(1 for r in admitted if not r["qhash"])
    wrong = 0
    wrong_2dp = 0
    judged = 0
    wrong_list = []
    tolerance_only = []
    right_scores, wrong_scores = [], []
    for r in admitted:
        if vault_by_sid:
            ans = vault_by_sid.get(r["sample_id"])
        else:
            ans = vault.get(r["qhash"]) if r["qhash"] else None
        if ans is None:
            continue
        judged += 1
        ra_ok = round_aware(to_num(r["certified"]), to_num(ans), ans)
        twodp_ok = label_match(r["certified"], ans)
        if not twodp_ok:
            wrong_2dp += 1
        if ra_ok and not twodp_ok:
            tolerance_only.append(r["sample_id"])
        if not ra_ok:
            wrong += 1
            c, v = to_num(r["certified"]), to_num(ans)
            gap = (abs(c - v) / max(1e-9, abs(v))) if (c is not None and v is not None) else None
            wrong_list.append(
                {
                    "sample_id": r["sample_id"],
                    "certified": r["certified"],
                    "vault_answer": ans,
                    "rel_gap": gap,
                    "score": r["score"],
                    "informative": r["informative"],
                }
            )
            wrong_scores.append(r["score"])
        else:
            right_scores.append(r["score"])
    fdr = wrong / judged if judged else None
    ub = clopper_pearson_upper(wrong, judged) if judged else None
    fdr2 = wrong_2dp / judged if judged else None
    ub2 = clopper_pearson_upper(wrong_2dp, judged) if judged else None
    from collections import Counter

    report = {
        "tau": tau,
        "tightening_rerun": a.tau is not None,
        "ruler_primary": "round_aware (paper's uniform scorer, rel 1e-4 "
        "+ label-decimals rounding)",
        "e1_accepts_total": accepts_total,
        "e1_accepts_without_base_value": accepts_no_value,
        "e1_accepts": len(rows),
        "admitted_after_calibration": len(admitted),
        "coverage_of_accepts": len(admitted) / len(rows),
        "judged_against_vault": judged,
        "admitted_missing_question_or_vault": len(admitted) - judged,
        "wrong_admissions_round_aware": wrong,
        "realized_fdr_point": fdr,
        "realized_fdr_95_upper": ub,
        "k3_point_pass_le_0.05": (fdr is not None and fdr <= 0.05),
        "k3_upper_pass_le_0.10": (ub is not None and ub <= 0.10),
        "sensitivity_2dp_ruler": {
            "wrong_admissions": wrong_2dp,
            "fdr_point": fdr2,
            "fdr_95_upper": ub2,
            "tolerance_only_disagreements": tolerance_only,
        },
        "admitted_score_hist_right": dict(Counter(right_scores)),
        "admitted_score_hist_wrong": dict(Counter(wrong_scores)),
        "wrong_admission_detail": wrong_list,
    }
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, indent=2))
    if missing_q:
        print(
            f"[replay] NOTE: {missing_q} admitted verdicts carry no "
            "question text; if verdict_full.json lacks a question field, "
            "rerun with --workorder-map to join by sample_id instead"
        )


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    w = sub.add_parser("workorder")
    w.add_argument("--nano", required=True)
    w.add_argument("--out", required=True)
    w.add_argument("--labels", required=True)
    w.add_argument("--n", type=int, default=150)
    w.add_argument("--seed", type=int, default=42)
    f = sub.add_parser("fit")
    f.add_argument(
        "--runs", required=True, help="certify runs dir containing <sid>/verdict_full.json"
    )
    f.add_argument("--labels", required=True)
    f.add_argument("--alpha", type=float, default=0.05)
    f.add_argument("--out", required=True)
    r = sub.add_parser("replay")
    r.add_argument("--calibration", required=True)
    r.add_argument("--e1-runs", required=True)
    r.add_argument(
        "--verdicts",
        required=True,
        help="compact GateOracle verdicts dir (authoritative "
        "certified values, e.g. outputs/e1/verdicts)",
    )
    r.add_argument(
        "--workorder", required=True, help="E1 gate work order jsonl (sample_id -> question join)"
    )
    r.add_argument("--vault", required=True)
    r.add_argument(
        "--tau",
        type=float,
        default=None,
        help="override the calibrated threshold (the one "
        "preregistered tightening rerun); flagged in report",
    )
    r.add_argument(
        "--exclude",
        default="sample_1,sample_2,sample_3,sample_4,sample_5",
        help="dev-split sample ids excluded from FDR accounting",
    )
    r.add_argument("--out", required=True)
    a = ap.parse_args()
    {"workorder": cmd_workorder, "fit": cmd_fit, "replay": cmd_replay}[a.cmd](a)


if __name__ == "__main__":
    main()
