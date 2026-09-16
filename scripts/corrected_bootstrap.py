#!/usr/bin/env python3
"""Paired stratified bootstrap for the E1 arms, uncorrected and corrected.

Purpose
    Compute the paired bootstrap intervals for the gate arm against every
    other arm on the 1,100 evaluation items (R0), and on item sets that
    remove the 85 selector-failure rows of the ground-truth arm on OptiBench
    (R1, the manuscript's sensitivity basis) or broader unions (R2, R3).

Pairing rule
    A paired bootstrap requires both arms to be scored on the identical item
    set. Dropping flagged rows from the ground-truth arm alone breaks the
    pairing, so every rule drops the same item ids from every arm. Removing
    items on which an arm failed mechanically helps that arm; here the arm
    helped is the baseline, so an interval that still excludes zero is the
    stronger claim.

Scoring
    round_aware is imported from scripts/score_eval.py, never reimplemented.

Inputs
    --arm NAME=PATH  repeatable; each PATH is <host>/outputs/e1/eval/<arm>,
                     the per-item trajectories.jsonl of one arm on all five
                     plates (private, not distributed: the trajectories carry
                     benchmark problem text)
    --seed           default 20260816; the manuscript intervals use --seed 42
    --reps           default 10000
    --out            default reanalysis
    --score-eval     path to score_eval.py, default auto-located under the
                     working directory (scripts/score_eval.py, in git)

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

Reproduce (from the repository root)
    python scripts/corrected_bootstrap.py run --arm gt=<host>/outputs/e1/eval/gt --arm vote=<host>/outputs/e1/eval/vote --arm runsok=<host>/outputs/e1/eval/runsok --arm gate=<host>/outputs/e1/eval/gate --reps 10000 --seed 42 --score-eval scripts/score_eval.py --out reanalysis/reviewer_round

Outputs
    intervals on stdout (captured as release/reviewer_round/04_bootstrap_raw.txt);
    <out>/excluded_ids.txt

Paper location
    Section 4.2 intervals and Appendix C.
"""

import argparse
import glob
import json
import os
import random
import sys
from collections import Counter, defaultdict

BENCH_HINTS = ["complexor", "industryor", "mamo", "optmath", "optibench"]

CORRECT_KEYS = ["correct", "is_correct", "judged_correct", "passed", "pass",
                "ok", "match", "round_aware_correct"]
PRED_KEYS = ["prediction", "pred", "predicted", "output", "final_answer"]
ANS_KEYS = ["answer", "label", "ground_truth", "optimal_value", "gt"]
ID_KEYS = ["sample_id", "id", "qid", "problem_id", "sample_key", "idx",
           "index", "name"]
FLAG_KEYS = ["e1_eval_failure", "eval_failure", "selector_failure"]


# ----------------------------------------------------------------------
# scoring: import the released ruler, never reimplement it
# ----------------------------------------------------------------------

def load_scorer(path, allow_fallback=False):
    """Import round_aware from score_eval.py so the ruler is bit-identical
    to the one every published number was produced with."""
    cands = []
    if path:
        cands.append(path)
    for root, _d, files in os.walk("."):
        if "score_eval.py" in files:
            cands.append(os.path.join(root, "score_eval.py"))
    for c in cands:
        if not c or not os.path.isfile(c):
            continue
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("score_eval", c)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            fn = getattr(mod, "round_aware", None)
            if fn is None:
                continue
            # round_aware(pred, ans_num, ans_raw) wants a NUMERIC second
            # argument; trajectory answers are strings ("200"), so passing the
            # raw label there raises TypeError inside rel_match and every row
            # scores False. score_eval.main() converts first:
            #   round_aware(to_num(prediction), to_num(answer), answer)
            # Mirror that exactly. The ruler itself stays the imported one.
            num = getattr(mod, "to_num", None)
            if num is None:
                print(f"  scorer: {c} has round_aware but no to_num; skipping")
                continue

            def _scored(pred, ans, ans_raw=None, _fn=fn, _num=num):
                raw = ans if ans_raw is None else ans_raw
                return bool(_fn(_num(pred), _num(ans), raw))

            print(f"  scorer: round_aware imported from {c}")
            return _scored, c
        except Exception as e:                     # noqa: BLE001
            print(f"  scorer: failed to import {c}: {e}")
    if not allow_fallback:
        print("\nFATAL: could not import round_aware from score_eval.py.\n"
              "Pass --score-eval <path>. Do NOT rerun with "
              "--allow-fallback-scorer unless you accept that a "
              "reimplemented ruler may disagree with the published numbers "
              "on boundary items.")
        return None, None
    print("  scorer: WARNING, using the fallback reimplementation. "
          "Every number below is suspect until the reconciliation passes.")

    def _to_num(x):
        if isinstance(x, (int, float)):
            return float(x)
        if not isinstance(x, str):
            return None
        t = x.strip().replace(",", "").replace("$", "")
        try:
            return float(t)
        except ValueError:
            return None

    def _dec(raw):
        t = raw if isinstance(raw, str) else repr(raw)
        return len(t.split(".")[1].rstrip()) if "." in t else 0

    def _fallback(pred, ans, ans_raw=None):
        p, a = _to_num(pred), _to_num(ans)
        if p is None or a is None:
            return False
        if abs(p - a) <= 1e-4 * max(abs(a), 1.0):
            return True
        d = _dec(ans_raw if ans_raw is not None else ans)
        return round(p, d) == round(a, d)

    return _fallback, "<fallback>"


def call_scorer(fn, pred, ans_raw):
    """score_eval.round_aware signatures vary; try the documented 3-arg form
    (raw label last, since decimal places are lost once it becomes a float)."""
    errs = []
    for args in ((pred, ans_raw, ans_raw), (pred, ans_raw)):
        try:
            return bool(fn(*args))
        except TypeError as e:
            errs.append(f"{len(args)}-arg: {e}")
            continue
        except Exception:                          # noqa: BLE001
            # A genuine scoring failure on one row is an error on that row.
            return False
    # No signature worked. Returning False here would silently score EVERY
    # row wrong and still print a full, well-formed report of zeros, which is
    # exactly how the previous version failed. Fail loudly instead.
    raise RuntimeError(
        "scorer signature mismatch, no row can be scored: " + "; ".join(errs))


def find_flag(obj, depth=0):
    """The failure flag may sit nested, and only appears on failing rows."""
    if depth > 3 or not isinstance(obj, dict):
        return False
    for k in FLAG_KEYS:
        if obj.get(k):
            return True
    for v in obj.values():
        if isinstance(v, dict) and find_flag(v, depth + 1):
            return True
    return False


def parse_arm(spec):
    if "=" not in spec:
        raise argparse.ArgumentTypeError(
            f"--arm expects NAME=PATH, got {spec!r}")
    name, path = spec.split("=", 1)
    return name.strip(), path.strip()


def bench_of(path):
    b = os.path.basename(path).lower()
    for h in BENCH_HINTS:
        if h in b:
            return h
    parent = os.path.basename(os.path.dirname(path)).lower()
    for h in BENCH_HINTS:
        if h in parent:
            return h
    return os.path.splitext(os.path.basename(path))[0]


def iter_rows(root, pattern="trajectories.jsonl"):
    """Only the per-item evaluation records. Whitelisting the filename is
    stricter and more stable than blacklisting runtime_logs/ and friends."""
    files = sorted(glob.glob(os.path.join(root, "**", pattern),
                             recursive=True))
    if not files:
        files = sorted(glob.glob(os.path.join(root, "**", "*.jsonl"),
                                 recursive=True))
        if files:
            print(f"  WARNING: no {pattern} under {root}; "
                  f"fell back to every .jsonl. Verify the counts.")
    for f in files:
        bench = bench_of(f)
        if f.endswith(".jsonl"):
            with open(f, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        yield bench, f, json.loads(line)
        else:
            obj = json.load(open(f, "r", encoding="utf-8"))
            rows = obj if isinstance(obj, list) else obj.get("rows", [])
            for r in rows:
                yield bench, f, r


def get_first(row, keys):
    for k in keys:
        if k in row:
            return k, row[k]
    return None, None


def to_bool_correct(v):
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "yes", "correct", "1", "pass"):
            return True
        if s in ("false", "no", "incorrect", "0", "fail", "wrong"):
            return False
    return None


def load_arm(root, pattern="trajectories.jsonl", scorer=None):
    """-> {bench: {item_id: (correct_bool, flagged_bool)}}

    Trajectory rows carry no boolean verdict, only prediction and answer, so
    correctness is computed here with the released round-aware ruler."""
    out = defaultdict(dict)
    unscored = Counter()
    for bench, _f, r in iter_rows(root, pattern):
        ik, iv = get_first(r, ID_KEYS)
        if ik is None:
            unscored["no id"] += 1
            continue
        ck, cv = get_first(r, CORRECT_KEYS)
        c = to_bool_correct(cv) if ck is not None else None
        if c is None:
            pk, pv = get_first(r, PRED_KEYS)
            ak, av = get_first(r, ANS_KEYS)
            if ak is None:
                unscored["no answer field"] += 1
                continue
            if scorer is None:
                unscored["no scorer"] += 1
                continue
            # an unparseable or missing prediction counts as an error
            c = False if pk is None or pv in (None, "") else \
                call_scorer(scorer, pv, av)
        out[bench][str(iv)] = (c, find_flag(r))
    if unscored:
        print(f"  rows skipped in {root}: {dict(unscored)}")
    return out


# ----------------------------------------------------------------------

def cmd_peek(a):
    scorer, _src = load_scorer(a.score_eval, a.allow_fallback_scorer)
    if scorer is None:
        return 1
    for name, root in a.arm:
        print(f"=== arm {name}  root {root} ===")
        if not os.path.isdir(root):
            print("  NOT A DIRECTORY")
            continue
        files = sorted(glob.glob(os.path.join(root, "**", a.rows),
                                 recursive=True))[:8]
        print(f"  jsonl files: {len(files)} shown")
        for f in files:
            print(f"    {f}  -> bench guess {bench_of(f)}")
        first = None
        for _b, _f, r in iter_rows(root, a.rows):
            first = r
            break
        if first is None:
            print("  NO ROWS PARSED")
            continue
        print("  row keys:", sorted(first.keys()))
        print("  id key   :", get_first(first, ID_KEYS)[0])
        print("  correct  :", get_first(first, CORRECT_KEYS))
        print("  prediction:", get_first(first, PRED_KEYS))
        print("  answer    :", get_first(first, ANS_KEYS))
        if scorer is not None:
            pv = get_first(first, PRED_KEYS)[1]
            av = get_first(first, ANS_KEYS)[1]
            print("  scored    :", call_scorer(scorer, pv, av))
        d = load_arm(root, a.rows, scorer)
        print("  loaded:", {b: len(v) for b, v in sorted(d.items())})
        print("  flagged:", {b: sum(1 for c, fl in v.values() if fl)
                             for b, v in sorted(d.items())})
    print("\nCounts must be 18/100/211/166/605 and the flagged line must show "
          "85 on optibench for the ground-truth arm. Anything else, STOP.")
    return 0


def macro_micro(arms, benches, ids_by_bench):
    macro, num, den = {}, Counter(), 0
    for name in arms:
        per = []
        tot_c = tot_n = 0
        for b in benches:
            ids = ids_by_bench[b]
            if not ids:
                per.append(0.0)
                continue
            c = sum(1 for i in ids if arms[name][b][i][0])
            per.append(100.0 * c / len(ids))
            tot_c += c
            tot_n += len(ids)
        macro[name] = (sum(per) / len(benches), 100.0 * tot_c / max(tot_n, 1))
    return macro


def bootstrap(arms, benches, ids_by_bench, reps, seed):
    rng = random.Random(seed)
    names = list(arms)
    keep = {b: list(ids_by_bench[b]) for b in benches}
    draws = {n: [] for n in names}
    micro_draws = {n: [] for n in names}
    for _ in range(reps):
        per = {n: [] for n in names}
        tot = {n: [0, 0] for n in names}
        for b in benches:
            pool = keep[b]
            k = len(pool)
            if k == 0:
                continue
            samp = [pool[rng.randrange(k)] for _ in range(k)]
            for n in names:
                c = sum(1 for i in samp if arms[n][b][i][0])
                per[n].append(100.0 * c / k)
                tot[n][0] += c
                tot[n][1] += k
        for n in names:
            draws[n].append(sum(per[n]) / len(per[n]))
            micro_draws[n].append(100.0 * tot[n][0] / max(tot[n][1], 1))
    return draws, micro_draws


def interval(diffs):
    d = sorted(diffs)
    n = len(d)
    lo = d[int(0.025 * n)]
    hi = d[int(0.975 * n) - 1]
    p = sum(1 for x in diffs if x > 0) / n
    return lo, hi, p


def report(tag, arms, benches, ids_by_bench, reps, seed, focus):
    mm = macro_micro(arms, benches, ids_by_bench)
    n_items = sum(len(ids_by_bench[b]) for b in benches)
    print(f"\n===== {tag}  ({n_items} items) =====")
    for n in arms:
        print(f"  {n:10s} macro {mm[n][0]:6.2f}   micro {mm[n][1]:6.2f}")
    draws, micro_draws = bootstrap(arms, benches, ids_by_bench, reps, seed)
    print(f"  paired stratified bootstrap, {reps} resamples, seed {seed}")
    for a, b in focus:
        if a not in arms or b not in arms:
            continue
        dm = [x - y for x, y in zip(draws[a], draws[b])]
        di = [x - y for x, y in zip(micro_draws[a], micro_draws[b])]
        lo, hi, p = interval(dm)
        lo2, hi2, p2 = interval(di)
        print(f"  {a} - {b}   macro {mm[a][0]-mm[b][0]:+5.2f}  "
              f"95% [{lo:+5.2f}, {hi:+5.2f}]  P(>0)={p:.4f}")
        print(f"  {'':{len(a)+len(b)+3}s}   micro {mm[a][1]-mm[b][1]:+5.2f}  "
              f"95% [{lo2:+5.2f}, {hi2:+5.2f}]  P(>0)={p2:.4f}")
    return mm


def cmd_run(a):
    scorer, src = load_scorer(a.score_eval, a.allow_fallback_scorer)
    if scorer is None:
        return 1
    arms = {}
    for name, root in a.arm:
        arms[name] = load_arm(root, a.rows, scorer)
    benches = sorted(set.intersection(*[set(v) for v in arms.values()]))
    print("benchmarks aligned across arms:", benches)

    common = {}
    for b in benches:
        sets = [set(arms[n][b]) for n in arms]
        common[b] = sorted(set.intersection(*sets))
        sizes = {n: len(arms[n][b]) for n in arms}
        print(f"  {b:12s} per-arm {sizes}  common {len(common[b])}")
    print("\nRECONCILIATION: common counts must be 18 / 100 / 211 / 166 / 605. "
          "If not, the arms are not aligned and every interval below is void.")

    focus = [(a.target, x) for x in arms if x != a.target]

    mm_raw = report("UNCORRECTED (as published)", arms, benches, common,
                    a.reps, a.seed, focus)
    print("\n  Check 1: the UNCORRECTED macro column must equal Table 2 "
          "exactly: gt 53.89, vote 54.82, runsok 56.51, gate 58.35.")
    print("  Check 2: gate-vote about +3.53 [+0.87, +6.75], gate-gt about "
          "+4.46 [+2.37, +6.64].")
    print("  Check 3: the R1 block must put gt macro at 55.95.")
    print("  Any of these failing means the row reader is wrong, not the "
          "paper. STOP and report.")

    def flagged_of(arm_names, plates):
        out = {b: set() for b in benches}
        for b in plates:
            for n in arm_names:
                for i in common[b]:
                    if arms[n][b][i][1]:
                        out[b].add(i)
        return out

    ref = a.rule_arm
    plate = [b for b in benches if a.rule_plate in b]
    rules = [
        ("R1 flagged rows of the %s arm on %s only  [PAPER BASIS]"
         % (ref, a.rule_plate), flagged_of([ref], plate)),
        ("R2 flagged rows of the %s arm on every plate" % ref,
         flagged_of([ref], benches)),
        ("R3 union of flagged rows across all arms, every plate",
         flagged_of(list(arms), benches)),
    ]

    for tag, fl in rules:
        n = sum(len(v) for v in fl.values())
        per = {b: len(fl[b]) for b in benches if fl[b]}
        kept = {b: [i for i in common[b] if i not in fl[b]] for b in benches}
        report("CORRECTED, %s  (removed %d: %s)" % (tag, n, per),
               arms, benches, kept, a.reps, a.seed, focus)

    flagged = rules[0][1]
    corrected = {b: [i for i in common[b] if i not in flagged[b]]
                 for b in benches}

    print("\nHOW TO READ THIS")
    print("  R1 is the basis the paper already prints. It must reproduce the")
    print("  published sensitivity numbers exactly (ground truth 73.5 on")
    print("  OptiBench, 55.95 macro). If it does, R1 is the interval to print")
    print("  and R2/R3 stay internal: they exist so you know where the")
    print("  boundary is, not so the paper reports three of everything.")
    print("  Every rule removes the same items from EVERY arm, which is what")
    print("  keeps the bootstrap paired. The correction favours the baseline,")
    print("  so an interval that still excludes zero is the stronger claim.")

    os.makedirs(a.out, exist_ok=True)
    with open(os.path.join(a.out, "excluded_ids.txt"), "w",
              encoding="utf-8") as fh:
        for b in benches:
            for i in sorted(flagged[b]):
                fh.write(f"{b}\t{i}\n")
    print(f"\nwrote {a.out}/excluded_ids.txt")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("peek", "run"):
        p = sub.add_parser(name)
        p.add_argument("--arm", action="append", type=parse_arm, required=True,
                       help="NAME=PATH, repeatable")
        p.add_argument("--target", default="gate",
                       help="arm compared against every other arm")
        p.add_argument("--reps", type=int, default=10000)
        p.add_argument("--seed", type=int, default=20260816)
        p.add_argument("--out", default="reanalysis")
        p.add_argument("--rule-arm", default="gt", dest="rule_arm",
                       help="arm whose flagged rows define the paper basis")
        p.add_argument("--rule-plate", default="optibench", dest="rule_plate",
                       help="plate the paper basis is restricted to")
        p.add_argument("--rows", default="trajectories.jsonl",
                       help="filename of the per-item eval records")
        p.add_argument("--score-eval", default=None, dest="score_eval",
                       help="path to score_eval.py; auto-located if omitted")
        p.add_argument("--allow-fallback-scorer", action="store_true",
                       dest="allow_fallback_scorer",
                       help="NOT recommended: reimplement the ruler instead "
                            "of importing the released one")
    a = ap.parse_args()
    return {"peek": cmd_peek, "run": cmd_run}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
