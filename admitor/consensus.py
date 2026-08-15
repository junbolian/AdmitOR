# -*- coding: utf-8 -*-
"""AdmitOR core -- consensus.py (v0.6.3)

L3: cross-family resampled differential consensus (the load-bearing wall).

Interface contract:
  Candidate(id, family, strategy, solve)
      solve(params: dict) -> SolveResult(objective, status)
      Only status == "optimal" enters comparison; anything else counts as a
      failure on that instantiation.
  Param spec, two accepted schemas per parameter:
      v0.3+ (preferred, base-anchored):
        {"base": x or [x...] or [[x...]...], "perturb": {"mode": "rel",
                              "r": 0.3, "integer": false}
                              or {"mode": "abs", "lo": a, "hi": b,
                                  "integer": false}}
        base may be a scalar, a vector, or an arbitrarily nested list
        (e.g. a cost matrix); perturbation is element-wise and
        shape-preserving.
      legacy:
        {"mode": "rel", "base": ..., "r": ...}
        {"mode": "range", "lo": a, "hi": b, "size": n, "integer": false}

Verdict semantics:
  ACCEPT        max clique spanning >= 2 model families over informative
                instances; clique value at instance 0 (unperturbed base, when
                available) is the deliverable answer.
  ABSTAIN       informative instances exist, but no cross-family clique.
  UNINFORMATIVE fewer than `min_informative` instances on which >= 2
                candidates solved to optimality; the sampling domain (or the
                candidate pool) must be repaired before any admission claim.
"""
import random
from dataclasses import dataclass, field
from itertools import combinations
from typing import Callable, Dict, List, Optional


@dataclass
class SolveResult:
    objective: Optional[float]
    status: str = "optimal"


@dataclass
class Candidate:
    id: str
    family: str
    strategy: str
    solve: Callable[[dict], SolveResult]


@dataclass
class L3Verdict:
    decision: str
    clique: List[str] = field(default_factory=list)
    families: List[str] = field(default_factory=list)
    instantiations: List[dict] = field(default_factory=list)
    objectives: Dict[str, list] = field(default_factory=dict)
    statuses: Dict[str, list] = field(default_factory=dict)
    informative: List[int] = field(default_factory=list)
    diagnoses: Dict[str, str] = field(default_factory=dict)
    disagreements: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


def base_params(spec: Dict[str, dict]) -> Optional[dict]:
    """Return the unperturbed original parameters if every entry carries a
    base value; otherwise None."""
    out = {}
    for name, s in spec.items():
        if "base" not in s:
            return None
        out[name] = s["base"]
    return out


def _perturb_rel(base, r, rng, integer=False):
    """Element-wise relative perturbation, recursing into nested lists
    (vectors, matrices, ...). Output has the same shape as `base`."""
    if isinstance(base, (list, tuple)):
        return [_perturb_rel(b, r, rng, integer) for b in base]
    v = base * rng.uniform(1 - r, 1 + r)
    return round(v) if integer else v


def _fill_abs(base, lo, hi, rng, integer=False):
    """Element-wise absolute resampling in [lo, hi], recursing into nested
    lists. Output has the same shape as `base` (scalar stays scalar)."""
    if isinstance(base, (list, tuple)):
        return [_fill_abs(b, lo, hi, rng, integer) for b in base]
    v = rng.uniform(lo, hi)
    return round(v) if integer else v


def _sample_one(base, mode_cfg, rng):
    if mode_cfg["mode"] == "rel":
        r = mode_cfg.get("r", 0.3)
        return _perturb_rel(base, r, rng, mode_cfg.get("integer", False))
    lo, hi = sorted((mode_cfg["lo"], mode_cfg["hi"]))
    return _fill_abs(base, lo, hi, rng, mode_cfg.get("integer", False))


def sample_params(spec: Dict[str, dict], rng: random.Random) -> dict:
    out = {}
    for name, s in spec.items():
        if "perturb" in s:
            out[name] = _sample_one(s["base"], s["perturb"], rng)
        elif s.get("mode") == "rel":
            out[name] = _sample_one(s["base"], {"mode": "rel", "r": s.get("r", 0.3)}, rng)
        elif s.get("mode") == "range":
            n = s.get("size", 1)
            lo, hi = sorted((s["lo"], s["hi"]))
            vals = [rng.uniform(lo, hi) for _ in range(n)]
            if s.get("integer"):
                vals = [round(v) for v in vals]
            out[name] = vals if n > 1 else vals[0]
        else:
            raise ValueError(f"unknown spec for {name}")
    return out


def _close(a: float, b: float, tol_rel: float) -> bool:
    return abs(a - b) <= tol_rel * max(1.0, abs(a), abs(b))


def _max_clique(ids: List[str], edge) -> List[str]:
    for k in range(len(ids), 0, -1):
        for combo in combinations(ids, k):
            if all(edge(a, b) for a, b in combinations(combo, 2)):
                return list(combo)
    return []


def run_l3(
    candidates: List[Candidate],
    spec: Dict[str, dict],
    m: int = 5,
    tol_rel: float = 1e-4,
    seed: int = 42,
    min_informative: int = 3,
) -> L3Verdict:
    rng = random.Random(seed)
    insts = [sample_params(spec, rng) for _ in range(m)]
    bp = base_params(spec)
    if bp is not None:
        insts.insert(0, bp)  # instance 0 = the original problem

    objs: Dict[str, list] = {}
    stats: Dict[str, list] = {}
    for c in candidates:
        orow, srow = [], []
        for p in insts:
            try:
                r = c.solve(p)
                ok = r.status == "optimal" and r.objective is not None
                orow.append(float(r.objective) if ok else None)
                srow.append(r.status)
            except Exception as e:  # pragma: no cover
                orow.append(None)
                srow.append("exception:" + type(e).__name__)
        objs[c.id], stats[c.id] = orow, srow

    ids = [c.id for c in candidates]
    fam = {c.id: c.family for c in candidates}
    n_inst = len(insts)

    informative = [k for k in range(n_inst) if sum(1 for i in ids if objs[i][k] is not None) >= 2]

    v = L3Verdict("", [], [], insts, objs, stats, informative)

    if len(informative) < min_informative:
        v.decision = "UNINFORMATIVE"
        v.notes.append(
            f"only {len(informative)} informative instantiation(s) "
            f"(needed {min_informative}); repair the sampling domain or the "
            f"candidate pool before judging"
        )
        return v

    def edge(a, b):
        for k in informative:
            za, zb = objs[a][k], objs[b][k]
            if za is None or zb is None or not _close(za, zb, tol_rel):
                return False
        return True

    clique = _max_clique(ids, edge)
    fams = sorted({fam[i] for i in clique})

    if clique and len(fams) >= 2:
        v.decision, v.clique, v.families = "ACCEPT", clique, fams
        ref = clique[0]
        for c in candidates:
            if c.id in clique:
                continue
            fails = [k for k in informative if objs[c.id][k] is None]
            if fails:
                v.diagnoses[c.id] = (
                    f"failed on informative instance(s) "
                    f"{[k for k in fails]}: "
                    f"{[stats[c.id][k] for k in fails]}"
                )
                continue
            deltas = [
                (k, abs(objs[c.id][k] - objs[ref][k]))
                for k in informative
                if objs[ref][k] is not None
            ]
            k, d = max(deltas, key=lambda t: t[1])
            v.diagnoses[c.id] = (
                f"diverges from consensus by {d:.4g} on instance {k} "
                f"(params: { {n: _short(val) for n, val in insts[k].items()} })"
            )
        return v

    v.decision = "ABSTAIN"
    for a, b in combinations(ids, 2):
        covalid = [k for k in informative if objs[a][k] is not None and objs[b][k] is not None]
        if not covalid:
            v.disagreements.append(f"{a} vs {b}: incomparable (no co-solved instance)")
            continue
        ks = [k for k in covalid if not _close(objs[a][k], objs[b][k], tol_rel)]
        if ks:
            v.disagreements.append(f"{a} vs {b}: diverge on instance(s) {ks}")
    return v


def _short(val, nd=2):
    if isinstance(val, (list, tuple)):
        return [_short(x, nd) for x in val]
    return round(val, nd) if isinstance(val, float) else val
