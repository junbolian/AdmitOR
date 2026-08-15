"""AdmitOR E1 -- e1_rebuild.py (v0.3)

Per-arm library rebuild. Ports the tail of the host's run_cluster
(pipeline/runner.py) verbatim: read relabeled trajectories, build into a
staging dir via AgentLoop.cluster_build, atomically replace the target
library. The host's machinery is imported unmodified; the only difference
from a native cluster run is that the input rows carry an arm's rewritten
ground truth and objective_metrics (produced by e1_relabel.py).

Inputs
    --relabeled     one arm's relabeled trajectories jsonl (from e1_relabel.py)
    --library       target skill-library directory to (re)build
    --cluster-eps, --cluster-min-samples, --archetype-fusion-alpha,
                    --agent-max-turns
                    library geometry, see the warning below
    --draft-budget  max characters of a cluster's draft inputs before
                    deterministic member subsampling (default 300000)

Outputs
    <library>/                        the rebuilt skill library
    <library>.build_summary.json      arm, record counts and the host's own
                                      build summary
    The same summary is echoed to stdout.

MUST be run from the OptSkills host checkout, because the host's imports
resolve against the current working directory:
  cd /path/to/OptSkills-main
  python /path/to/AdmitOR/scripts/e1_rebuild.py \
      --relabeled outputs/e1/arms/vote.jsonl \
      --library outputs/e1/libs/skill_library_vote \
      --cluster-eps <same as collect run> --cluster-min-samples <same> \
      [--analysis-workers 4] [--builder-workers 4] \
      [--archetype-fusion-alpha 0.55] [--agent-max-turns 12]

Pass EXACTLY the eps / min-samples / alpha the collect run used (read them
from the collect run's resume.json or main.py defaults) -- library geometry
must be identical across arms or the comparison is confounded.
Cost note: cluster_build calls the LLM for per-candidate skill analysis;
this is the per-arm rebuild cost, identical across arms by construction.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys


def _install_size_guard(budget_chars: int) -> None:
    """Monkeypatch SkillBuilder.build_raw_skill with a draft-size guard.

    Root cause being addressed: optmath-train problems are template-generated,
    so embeddings of same-template items are near-duplicates and DBSCAN
    (eps 0.05, min_samples 1) can merge whole template families into one
    giant cluster. The host assembles that cluster's ENTIRE ingredients +
    analyses into a single draft prompt with no size cap; the relay answers
    megabyte-scale request bodies by closing the connection, which surfaces
    as "Remote end closed connection without response" -- a deterministic
    poison request wearing a network error's clothes.

    The guard measures the draft inputs before the LLM call. Under budget:
    untouched passthrough. Over budget: deterministic subsample of cluster
    members (seeded by cluster name, one fixed shuffle, nested prefixes) so
    the skill is distilled from a representative subset. Applied identically
    to all four arms => symmetric, documented protocol deviation. Logging
    only otherwise; host files unmodified (patch lives in this driver).
    """
    import random

    from skill_core import skill_builder as sb

    original = sb.SkillBuilder.build_raw_skill

    def _size(x) -> int:
        try:
            return len(json.dumps(x, ensure_ascii=False, default=str))
        except Exception:
            return len(str(x))

    def guarded(self, cluster_name, ingredients, analyses):
        total = _size(ingredients) + _size(analyses)
        print(f"[size_guard] {cluster_name}: draft inputs {total} chars")
        if total <= budget_chars:
            return original(self, cluster_name, ingredients, analyses)
        if isinstance(analyses, list) and len(analyses) > 1:
            paired = isinstance(ingredients, list) and len(ingredients) == len(analyses)
            rng = random.Random(f"admitor:{cluster_name}")
            order = list(range(len(analyses)))
            rng.shuffle(order)
            k = len(order)
            while True:
                pick = sorted(order[:k])
                sub_an = [analyses[i] for i in pick]
                sub_in = [ingredients[i] for i in pick] if paired else ingredients
                now = _size(sub_in) + _size(sub_an)
                if now <= budget_chars or k == 1:
                    print(
                        f"[size_guard] {cluster_name}: OVER BUDGET, "
                        f"kept {k}/{len(order)} members ({now} chars)"
                    )
                    return original(self, cluster_name, sub_in, sub_an)
                k = max(1, int(k * 0.7))
        raise RuntimeError(
            f"[size_guard] {cluster_name}: draft inputs {total} chars exceed "
            f"budget {budget_chars} and are not subsamplable "
            f"(ingredients={type(ingredients).__name__}, "
            f"analyses={type(analyses).__name__}) -- paste this line back"
        )

    sb.SkillBuilder.build_raw_skill = guarded
    print(f"[size_guard] installed, budget={budget_chars} chars")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--relabeled", required=True)
    ap.add_argument("--library", required=True)
    ap.add_argument("--cluster-eps", required=True, type=float)
    ap.add_argument("--cluster-min-samples", required=True, type=int)
    ap.add_argument("--analysis-workers", type=int, default=4)
    ap.add_argument("--builder-workers", type=int, default=4)
    ap.add_argument("--archetype-fusion-alpha", type=float, default=0.55)
    ap.add_argument("--agent-max-turns", type=int, default=12)
    ap.add_argument(
        "--draft-budget",
        type=int,
        default=300000,
        help="max chars of a cluster's draft inputs before " "deterministic member subsampling",
    )
    a = ap.parse_args()

    sys.path.insert(0, os.getcwd())  # run from OptSkills-main
    try:
        from agents.agent_loop import AgentLoop
    except ImportError as err:
        raise SystemExit(
            f"host imports failed ({err}) -- run this with the OptSkills "
            f"host checkout as the current working directory"
        ) from err
    _install_size_guard(a.draft_budget)

    with open(a.relabeled, encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]
    arms = {str(r.get("e1_arm", "")) for r in records}
    if len(arms) != 1 or "" in arms:
        raise SystemExit(f"input must be one arm's relabeled file; saw {arms}")
    arm = arms.pop()
    eligible = sum(1 for r in records if r.get("eligible"))
    print(f"[e1_rebuild] arm={arm} records={len(records)} eligible={eligible}")

    staging = a.library + ".building"
    if os.path.isdir(staging):
        shutil.rmtree(staging)
    loop = AgentLoop(
        skill_library_dir=staging,
        archetype_fusion_alpha=a.archetype_fusion_alpha,
        agent_max_turns=a.agent_max_turns,
        analysis_workers=a.analysis_workers,
        builder_workers=a.builder_workers,
        logger=None,
    )
    summary = loop.cluster_build(records, a.cluster_eps, a.cluster_min_samples)
    if os.path.isdir(a.library):
        shutil.rmtree(a.library)
    os.makedirs(os.path.dirname(os.path.abspath(a.library)), exist_ok=True)
    os.replace(staging, a.library)
    out = {
        "arm": arm,
        "records": len(records),
        "eligible": eligible,
        "library": a.library,
        "build_summary": summary,
    }
    with open(a.library + ".build_summary.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2, default=str)
    print(json.dumps(out, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
