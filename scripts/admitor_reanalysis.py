#!/usr/bin/env python3
"""
AdmitOR re-analysis driver. Zero model calls: reads stored certification
artifacts plus the sealed vault only.

Subcommands
-----------
peek   dump the actual schema of one verdict_full.json and one vault line.
score  continuous-evidence separation: tests whether ANY continuous statistic
       of the clique separates the wrong admissions from the correct ones
       (AUC per statistic, best threshold reaching FDR <= alpha at a minimum
       coverage).
relax  cross-family counterfactual. Recomputes verdicts with the >=2-family
       requirement dropped and with a 3-family requirement, on stored data.
uninf  problem-level decomposition of the UNINFORMATIVE outcomes.

Inputs (all in git)
    --runs           artifacts/e1/certify_runs (verdict_full.json per sample)
    --vault          datasets/vault/optmath-train-300-labels.jsonl
    --only-samples   release/reviewer_round/admitted_ids_wild_138.txt for the
                     138 problems admitted at the calibrated threshold
    --out            default reanalysis/reviewer_round

Reproduce (from the repository root)
    python scripts/admitor_reanalysis.py score --only-samples release/reviewer_round/admitted_ids_wild_138.txt
    python scripts/admitor_reanalysis.py relax --only-samples release/reviewer_round/admitted_ids_wild_138.txt

Outputs
    score: a per-statistic table on stdout; <out>/admitted_rows.json and
    <out>/wrong_ids.txt. relax and uninf: stdout (uninf also writes
    <out>/uninformative.json).

Paper location
    Section 4.3: no continuous statistic of the clique reaches FDR <= 5% at
    >= 50% coverage on the 138 admitted problems (best AUC 0.635, neg_tight).
    The threshold sweep of Section 4.3 (15.9% / 16.5% / 16.0% / 14.7%) is
    produced by e3_calibrate.py replay --tau, not by this script.
"""

import argparse
import glob
import json
import math
import os
import sys
from collections import Counter, defaultdict

REL_TOL = 1e-6          # value-equality tolerance used by the gate
SCORER_TOL = 1e-4       # round-aware scorer relative tolerance


# ----------------------------------------------------------------------
# loading
# ----------------------------------------------------------------------

def find_verdicts(runs_dir):
    pats = [
        os.path.join(runs_dir, "**", "verdict_full.json"),
        os.path.join(runs_dir, "**", "*verdict*.json"),
    ]
    seen, out = set(), []
    for p in pats:
        for f in glob.glob(p, recursive=True):
            if f not in seen:
                seen.add(f)
                out.append(f)
        if out:
            break
    return sorted(out)


def load_json(path):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def sample_id_of(path, obj):
    for k in ("sample_id", "id", "problem_id", "qid", "name"):
        v = obj.get(k)
        if isinstance(v, str) and v:
            return v
    parent = os.path.basename(os.path.dirname(path))
    return parent or os.path.splitext(os.path.basename(path))[0]


def load_vault(path):
    """Vault jsonl. Joins on sample_id, else on idx, else on 1-based order."""
    by_id, by_idx, ordered = {}, {}, []
    with open(path, "r", encoding="utf-8") as fh:
        for n, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            ans = None
            for k in ("answer", "optimal_value", "ground_truth", "label", "value"):
                if k in r and r[k] not in ("", None):
                    ans = r[k]
                    break
            try:
                ans = float(ans)
            except (TypeError, ValueError):
                ans = None
            ordered.append(ans)
            for k in ("sample_id", "id", "problem_id", "name"):
                if isinstance(r.get(k), str) and r[k]:
                    by_id[r[k]] = ans
            if "idx" in r:
                by_idx[str(r["idx"])] = ans
    return by_id, by_idx, ordered


def vault_lookup(sid, by_id, by_idx, ordered):
    if sid in by_id:
        return by_id[sid]
    digits = "".join(c for c in sid if c.isdigit())
    if digits:
        if digits in by_idx:
            return by_idx[digits]
        i = int(digits)
        for cand in (i, i - 1):
            if 0 <= cand < len(ordered):
                return ordered[cand]
    return None


# ----------------------------------------------------------------------
# schema adaptation
# ----------------------------------------------------------------------

def get_tables(v):
    """Return (objectives, statuses, families) as dicts keyed by candidate id.

    Expected layout (k4_matrix v0.2): top-level parallel dicts. Falls back to
    a per-candidate record list. Returns None if neither shape is present.
    """
    def pick(*keys):
        for k in keys:                 # explicit None test: an empty list is a
            if v.get(k) is not None:   # legitimate value on UNINFORMATIVE rows
                return v[k]
        return None

    obj = pick("objectives", "values", "objective_values")
    sta = pick("statuses", "status")
    fam = pick("families", "family")
    if isinstance(obj, dict) and isinstance(fam, dict):
        return obj, (sta if isinstance(sta, dict) else {}), fam

    # Real AdmitOR schema: "families" is the LIST of family names covered by
    # the clique, not a per-candidate map. Candidate ids are A-direct /
    # B-structured / C-direct, so the family key is the id prefix. This is the
    # same convention e3_calibrate.verdict_score uses: {str(m)[:1] for m in clique}.
    if isinstance(obj, dict) and isinstance(fam, (list, tuple, set)):
        derived = {cid: str(cid)[:1] for cid in obj}
        return obj, (sta if isinstance(sta, dict) else {}), derived

    cands = v.get("candidates") or v.get("panel") or v.get("arms")
    if isinstance(cands, list) and cands and isinstance(cands[0], dict):
        obj, sta, fam = {}, {}, {}
        for i, c in enumerate(cands):
            cid = str(c.get("id", c.get("name", i)))
            obj[cid] = c.get("objectives", c.get("values"))
            sta[cid] = c.get("statuses", c.get("status"))
            fam[cid] = c.get("family", c.get("arm"))
        return obj, sta, fam
    return None, None, None


def as_series(x):
    """Normalise a per-instance record to an ordered list."""
    if x is None:
        return []
    if isinstance(x, list):
        return x
    if isinstance(x, dict):
        def key(k):
            try:
                return (0, int(k))
            except ValueError:
                return (1, k)
        return [x[k] for k in sorted(x, key=key)]
    return [x]


def fnum(x):
    try:
        f = float(x)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError):
        return None


def clique_members(v, fam):
    for k in ("clique", "clique_members", "accepted_candidates", "quorum"):
        c = v.get(k)
        if isinstance(c, list) and c:
            return [str(x) for x in c]
        if isinstance(c, dict) and c.get("members"):
            return [str(x) for x in c["members"]]
    return []


def verdict_of(v):
    for k in ("verdict", "decision", "outcome", "status"):
        val = v.get(k)
        if isinstance(val, str):
            return val.strip().upper()
    return "UNKNOWN"


def clique_value(v):
    for k in ("clique_value", "certified_value", "value", "base_value"):
        f = fnum(v.get(k))
        if f is not None:
            return f
    # Real AdmitOR schema stores no certified value. It is the first clique
    # member's objective at instance 0, which is what e1_certify.py writes into
    # the compact verdict. Without this fallback is_wrong() returns None on
    # every row.
    obj = v.get("objectives")
    cl = v.get("clique")
    if isinstance(obj, dict) and isinstance(cl, list) and cl:
        series = as_series(obj.get(str(cl[0])))
        if series:
            return fnum(series[0])
    return None


# ----------------------------------------------------------------------
# peek
# ----------------------------------------------------------------------

def cmd_peek(a):
    files = find_verdicts(a.runs)
    print(f"found {len(files)} verdict files under {a.runs}")
    if not files:
        print("NOTHING FOUND. Check --runs, or pass the directory that holds "
              "the per-sample subfolders.")
        return 1
    v = load_json(files[0])
    print(f"\n--- {files[0]} ---")
    print("top-level keys:", sorted(v.keys()))
    for k in sorted(v.keys()):
        val = v[k]
        if isinstance(val, dict):
            ks = list(val.keys())[:4]
            print(f"  {k}: dict[{len(val)}] sample keys {ks}")
            if ks:
                inner = val[ks[0]]
                t = type(inner).__name__
                prev = inner if not isinstance(inner, (list, dict)) else (
                    inner[:4] if isinstance(inner, list) else list(inner)[:4])
                print(f"      {ks[0]} -> {t}: {prev}")
        elif isinstance(val, list):
            print(f"  {k}: list[{len(val)}] first={val[0] if val else None!r}")
        else:
            print(f"  {k}: {type(val).__name__} = {val!r}")
    obj, sta, fam = get_tables(v)
    print("\nadapter result:",
          "OK" if obj else "FAILED, paste the block above back")
    if obj:
        print("  candidate ids:", list(obj.keys()))
        print("  families:", fam)
        print("  objective series lengths:",
              {c: len(as_series(obj[c])) for c in obj})
        print("  verdict:", verdict_of(v), " clique:", clique_members(v, fam),
              " clique_value:", clique_value(v))
    if a.vault:
        with open(a.vault, "r", encoding="utf-8") as fh:
            first = fh.readline().strip()
        print("\nvault first line keys:", sorted(json.loads(first).keys()))
    return 0


# ----------------------------------------------------------------------
# shared: build the admitted table
# ----------------------------------------------------------------------

def read_id_list(path):
    if not path:
        return None
    out = set()
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            t = line.strip()
            if t and not t.startswith("#"):
                out.add(t)
    return out


def build_rows(runs_dir, vault_path, only=None, exclude=None):
    by_id, by_idx, ordered = load_vault(vault_path)
    rows, skipped = [], Counter()
    for f in find_verdicts(runs_dir):
        v = load_json(f)
        sid = sample_id_of(f, v)
        if only is not None and sid not in only:
            skipped["not in --only-samples"] += 1
            continue
        if exclude is not None and sid in exclude:
            skipped["in --exclude-samples"] += 1
            continue
        obj, sta, fam = get_tables(v)
        if obj is None:
            skipped["schema"] += 1
            continue
        verdict = verdict_of(v)
        cv = clique_value(v)
        members = clique_members(v, fam) or []
        series = {c: [fnum(x) for x in as_series(obj[c])] for c in obj}
        nmax = max((len(s) for s in series.values()), default=0)

        stored_inf = v.get("informative")
        if isinstance(stored_inf, int):
            informative = stored_inf          # the count the gate itself used
        elif isinstance(stored_inf, list):
            informative = len(stored_inf)
        else:
            informative = 0
            for j in range(nmax):
                vals = [series[c][j] for c in series
                        if j < len(series[c]) and series[c][j] is not None]
                if len(vals) >= 3:
                    informative += 1

        cl = [c for c in members if c in series] or [
            c for c in series if all(x is not None for x in series[c])]
        fams = sorted({str(fam.get(c)) for c in cl if fam.get(c) is not None})

        # continuous evidence statistics over the clique's value trace
        trace = []
        for j in range(nmax):
            vals = [series[c][j] for c in cl
                    if j < len(series[c]) and series[c][j] is not None]
            if len(vals) == len(cl) and cl:
                trace.append(vals)

        def rel(x, y):
            d = max(abs(x), abs(y), 1e-12)
            return abs(x - y) / d

        tight = max((max(rel(a_, b_) for a_ in vs for b_ in vs)
                     for vs in trace), default=None)
        means = [sum(vs) / len(vs) for vs in trace]
        if len(means) >= 2:
            lo, hi = min(means), max(means)
            rng = (hi - lo) / max(abs(hi), abs(lo), 1e-12)
        else:
            rng = 0.0

        outside = [c for c in series if c not in cl]
        seps = []
        for j in range(min(nmax, len(means))):
            for c in outside:
                if j < len(series[c]) and series[c][j] is not None:
                    seps.append(rel(series[c][j], means[j]))
        sep = max(seps) if seps else None

        gt = vault_lookup(sid, by_id, by_idx, ordered)
        rows.append(dict(
            sample=sid, verdict=verdict, value=cv, gt=gt,
            n_fam=len(fams), fams=fams, clique_size=len(cl),
            informative=informative, n_cand=len(series),
            tight=tight, trace_range=rng, sep=sep,
            n_trace=len(trace), file=f,
            deployed_score=10 * len(fams) + len(cl) + informative / 10.0,
        ))
    return rows, skipped


def is_wrong(r):
    if r["value"] is None or r["gt"] is None:
        return None
    d = max(abs(r["value"]), abs(r["gt"]), 1e-12)
    return abs(r["value"] - r["gt"]) / d > SCORER_TOL


def auc(pos, neg):
    """P(score of a wrong case < score of a right case), ties at 0.5."""
    if not pos or not neg:
        return float("nan")
    n = 0.0
    for a_ in pos:
        for b_ in neg:
            n += 1.0 if a_ < b_ else (0.5 if a_ == b_ else 0.0)
    return n / (len(pos) * len(neg))


# ----------------------------------------------------------------------
# score
# ----------------------------------------------------------------------

def cmd_score(a):
    rows, skipped = build_rows(a.runs, a.vault,
                               read_id_list(a.only_samples),
                               read_id_list(a.exclude_samples))
    adm = [r for r in rows if r["verdict"].startswith("ACCEPT")]
    lab = [(r, is_wrong(r)) for r in adm]
    lab = [(r, w) for r, w in lab if w is not None]
    wrong = [r for r, w in lab if w]
    right = [r for r, w in lab if not w]
    print(f"verdict files: {len(rows)}  accepted: {len(adm)}  "
          f"joined to vault: {len(lab)}  wrong: {len(wrong)}  right: {len(right)}")
    if skipped:
        print("skipped:", dict(skipped))
    print("\nRECONCILIATION. Compare against the published counts before "
          "trusting anything below.")
    print("  with no --only-samples: expect 174 ACCEPT over the full stream, "
          "170 after the 5-problem dev split.")
    print("  with --only-samples set to the 138 tau-admitted ids: expect "
          "138 joined and 22 wrong under the round-aware ruler.")
    print("  If the counts do not match, the vault join or the id filter is "
          "wrong. STOP and report, do not reinterpret.")
    if not wrong or not right:
        print("cannot compute separation without both classes; run peek.")
        return 1

    stats = [
        ("n_fam", lambda r: r["n_fam"], True),
        ("clique_size", lambda r: r["clique_size"], True),
        ("informative", lambda r: r["informative"], True),
        ("trace_range", lambda r: r["trace_range"], True),
        ("neg_tight", lambda r: -(r["tight"] or 0.0), True),
        ("sep", lambda r: (r["sep"] if r["sep"] is not None else 0.0), True),
        ("n_trace", lambda r: r["n_trace"], True),
        ("deployed_score", lambda r: r["deployed_score"], True),
    ]

    print("\nAUC = P(wrong case scores below a correct case). 0.5 = no signal.")
    print(f"A separator must also retain at least {a.min_coverage:.0%} of the "
          "admitted set to count.")
    print(f"{'statistic':14s} {'AUC':>6s} {'best FDR<=5%':>14s} {'coverage':>9s}")
    const_note = []
    best_overall = None
    for name, fn, _ in stats:
        pv = [fn(r) for r in wrong]
        nv = [fn(r) for r in right]
        A = auc(pv, nv)
        if len(set(pv + nv)) == 1:
            const_note.append(name)
        # sweep every attainable threshold, keep the one hitting FDR<=alpha
        allv = sorted(set(pv + nv))
        best = None
        for t in allv:
            keep_w = sum(1 for x in pv if x >= t)
            keep_r = sum(1 for x in nv if x >= t)
            k = keep_w + keep_r
            if k == 0:
                continue
            fdr = keep_w / k
            if (fdr <= a.alpha and k >= a.min_coverage * len(lab)
                    and (best is None or k > best[2])):
                best = (t, fdr, k)
        if best:
            print(f"{name:14s} {A:6.3f} {best[1]*100:13.1f}% "
                  f"{best[2]/len(lab)*100:8.1f}%")
        else:
            print(f"{name:14s} {A:6.3f} {'unreachable':>14s} {'-':>9s}")
        if best_overall is None or (best and best[2] > best_overall[3]):
            if best:
                best_overall = (name, best[0], best[1], best[2])

    if const_note:
        print("\nCONSTANT on the admitted set, so they carry no separating "
              "information here by construction: " + ", ".join(const_note))
    print("\nVERDICT")
    if best_overall is None:
        print(f"  No single continuous statistic reaches FDR <= {a.alpha:.0%} at "
              f"usable coverage (>= {a.min_coverage:.0%}). The K3 conclusion "
              "is not an artifact of the four-atom score, and this sentence "
              "can go into 4.3.")
    else:
        print(f"  {best_overall[0]} reaches FDR {best_overall[2]*100:.1f}% at "
              f"{best_overall[3]} admissions. This WEAKENS the current text: "
              "a continuous score does separate, and 4.3 must say so.")

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "admitted_rows.json"), "w",
              encoding="utf-8") as fh:
        json.dump([{k: v for k, v in r.items() if k != "file"}
                   for r, _ in lab], fh, indent=2, default=str)
    with open(os.path.join(a.out, "wrong_ids.txt"), "w",
              encoding="utf-8") as fh:
        fh.write("\n".join(r["sample"] for r in wrong) + "\n")
    print(f"\nwrote {a.out}/admitted_rows.json and {a.out}/wrong_ids.txt")
    return 0


# ----------------------------------------------------------------------
# relax
# ----------------------------------------------------------------------

def cmd_relax(a):
    rows, _ = build_rows(a.runs, a.vault,
                         read_id_list(a.only_samples),
                         read_id_list(a.exclude_samples))
    adm = [r for r in rows if r["verdict"].startswith("ACCEPT")]
    lab = [(r, is_wrong(r)) for r in adm]
    lab = [(r, w) for r, w in lab if w is not None]

    print("Cross-family requirement counterfactual, on stored verdicts only.\n")
    print(f"{'rule':28s} {'admitted':>9s} {'wrong':>6s} {'precision':>10s}")
    for name, pred in [
        ("as deployed (>=2 families)", lambda r: r["n_fam"] >= 2),
        ("relaxed (any 2 candidates)", lambda r: r["clique_size"] >= 2),
        ("strict (>=3 families)", lambda r: r["n_fam"] >= 3),
        ("relaxed + 3-member clique", lambda r: r["clique_size"] >= 3),
    ]:
        sel = [(r, w) for r, w in lab if pred(r)]
        n = len(sel)
        w = sum(1 for _, x in sel if x)
        p = (n - w) / n if n else float("nan")
        print(f"{name:28s} {n:9d} {w:6d} {p:10.3f}")

    same_fam = [(r, w) for r, w in lab if r["n_fam"] < 2 and r["clique_size"] >= 2]
    print(f"\ncliques that a family-agnostic rule would add: {len(same_fam)}"
          f"  wrong among them: {sum(1 for _, w in same_fam if w)}")
    if same_fam:
        print("  These are the cases the cross-family requirement is buying. "
              "Report the count and their precision in 4.2.")
    else:
        print("  The cross-family requirement is never binding in this pilot. "
              "Say so explicitly rather than leaving it implied; a reviewer "
              "who finds this unaided will read it as an untested design claim.")
    return 0


# ----------------------------------------------------------------------
# uninf
# ----------------------------------------------------------------------

def cmd_uninf(a):
    reasons = Counter()
    detail = []
    only = read_id_list(a.only_samples)
    exclude = read_id_list(a.exclude_samples)
    for f in find_verdicts(a.runs):
        v = load_json(f)
        sid = sample_id_of(f, v)
        if only is not None and sid not in only:
            continue
        if exclude is not None and sid in exclude:
            continue
        if not verdict_of(v).startswith("UNINFORM"):
            continue
        obj, sta, fam = get_tables(v)
        if obj is None:
            reasons["schema_unreadable"] += 1
            continue
        series = {c: [fnum(x) for x in as_series(obj[c])] for c in obj}
        stat = {c: [str(x).lower() for x in as_series(sta.get(c))]
                for c in obj} if sta else {}
        nmax = max((len(s) for s in series.values()), default=0)
        informative = sum(
            1 for j in range(nmax)
            if len([1 for c in series
                    if j < len(series[c]) and series[c][j] is not None]) >= 3)
        dead = [c for c in series if all(x is None for x in series[c])]
        flat = Counter()
        for c in stat:
            for s in stat[c]:
                if "infeas" in s or "unbounded" in s:
                    flat["infeasible"] += 1
                elif "crash" in s or "error" in s or "exception" in s:
                    flat["crash"] += 1
                elif "fail" in s:
                    flat["failed"] += 1
        if len(dead) >= 2:
            reasons["two or more candidates never returned a value"] += 1
        elif flat.get("infeasible", 0) >= flat.get("crash", 0):
            reasons["dominated by infeasible resampled instances"] += 1
        elif flat.get("crash", 0) > 0:
            reasons["dominated by candidate execution failure"] += 1
        else:
            reasons["other / too few informative instances"] += 1
        detail.append(dict(sample=sid, informative=informative,
                           dead_candidates=len(dead), status_counts=dict(flat)))

    total = sum(reasons.values())
    print(f"UNINFORMATIVE problems: {total}\n")
    for k, n in reasons.most_common():
        print(f"  {n:4d}  {k}")
    print("\nSentence for 4.2: of the 114 UNINFORMATIVE outcomes, "
          "<n1> arise from candidate execution failure and <n2> from "
          "infeasible resampled instances, so coverage is limited by the "
          "harness rather than by conflicting evidence.")
    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "uninformative.json"), "w",
              encoding="utf-8") as fh:
        json.dump(detail, fh, indent=2)
    print(f"\nwrote {a.out}/uninformative.json")
    return 0


# ----------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("peek", "score", "relax", "uninf"):
        p = sub.add_parser(name)
        p.add_argument("--runs", default="artifacts/e1/certify_runs",
                       help="directory containing certification runs")
        p.add_argument("--vault", default="datasets/vault/optmath-train-300-labels.jsonl",
                       help="sealed vault jsonl")
        p.add_argument("--out", default="reanalysis/reviewer_round", help="output directory")
        p.add_argument("--alpha", type=float, default=0.05)
        p.add_argument("--min-coverage", type=float, default=0.5,
                       dest="min_coverage",
                       help="fraction of admissions a separator must retain")
        p.add_argument("--only-samples", default=None, dest="only_samples",
                       help="file of sample ids, one per line; restricts the "
                            "analysis to those problems (use the 138 "
                            "tau-admitted ids to reproduce the paper's set)")
        p.add_argument("--exclude-samples", default=None,
                       dest="exclude_samples",
                       help="file of sample ids to drop, e.g. the dev split")
    a = ap.parse_args()
    if a.cmd in ("score", "relax") and not a.vault:
        ap.error(f"{a.cmd} requires --vault")
    return {"peek": cmd_peek, "score": cmd_score,
            "relax": cmd_relax, "uninf": cmd_uninf}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())