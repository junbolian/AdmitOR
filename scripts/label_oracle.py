"""AdmitOR E1 -- label_oracle.py (v0.1)

Four judges for the E1 replay, all expressed as EFFECTIVE-GROUND-TRUTH
functions over a shared collect trajectory row (OptSkills --phase cluster
output). Rewriting the row's ground truth and re-running the host's own
attach_objective_metrics reproduces each arm's verdicts through unmodified
host logic -- the judge is swapped, the judging machinery is not.

Arms:
  gt      answers from the sealed vault (published labels as-is, D16)
  vote    majority vote over the sample's own rollout candidates (2dp)
  runsok  code-ran-equals-positive (host's native blind-mode behavior)
  gate    AdmitOR certification verdicts (ACCEPT clique value or reject)

Host-judging semantics replicated verbatim from
skill_core/trajectory_analyzer.py: success = returncode 0 with a result;
positive = 2dp HALF_UP string equality, fallback abs_gap <= 0.005.

NO_CONSENSUS sentinel: a numeric ground truth no finite candidate matches
(1e308). Non-numeric sentinels would fall through the host's empty-gt
branch and silently degrade to runs-ok semantics; 1e308 keeps every
candidate negative and the sample ineligible.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from collections import Counter
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

NO_CONSENSUS = "1e308"
DEV_SPLIT_INDICES = {1, 2, 3, 4, 5}  # optmath-train items 1-5, excluded from E1 accounting


# ---- host-faithful judging primitives (port of trajectory_analyzer) -------


def to_numeric(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_2dp_half_up(value: Any) -> Optional[str]:
    try:
        quantized = Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError, TypeError):
        return None
    return format(quantized, "f")


def candidate_success(candidate: Dict[str, Any]) -> bool:
    run_result = candidate.get("run_result", {})
    if not isinstance(run_result, dict):
        return False
    return run_result.get("returncode") == 0 and run_result.get("result") is not None


def candidate_result(candidate: Dict[str, Any]) -> Any:
    run_result = candidate.get("run_result", {})
    return run_result.get("result") if isinstance(run_result, dict) else None


def host_label(candidate: Dict[str, Any], ground_truth: str) -> str:
    """Exactly the host's default_label under the given ground truth."""
    gt_text = str(ground_truth).strip()
    success = candidate_success(candidate)
    if not success:
        return "negative"
    if not gt_text:
        return "positive"  # host blind-mode fallback: success => positive
    gt_num = to_numeric(gt_text)
    pred_num = to_numeric(candidate_result(candidate))
    pred_2dp = round_2dp_half_up(pred_num) if pred_num is not None else None
    gt_2dp = round_2dp_half_up(gt_num) if gt_num is not None else None
    if pred_2dp and gt_2dp:
        return "positive" if pred_2dp == gt_2dp else "negative"
    if pred_num is not None and gt_num is not None:
        return "positive" if abs(pred_num - gt_num) <= 0.005 else "negative"
    return "negative"


def attach_metrics(candidate: Dict[str, Any], ground_truth: str) -> Dict[str, Any]:
    """Recompute objective_metrics under a new ground truth, mirroring the
    host's attach_objective_metrics field-for-field. The host's downstream
    (default_label inside cluster_build) reads these stored metrics, so the
    relabel step MUST rewrite them -- rewriting only the answer field would
    leave stale blind-mode metrics and silently degrade every arm to
    runs-ok semantics at rebuild time."""
    gt_text = str(ground_truth).strip()
    gt_num = to_numeric(gt_text) if gt_text else None
    run_result = candidate.get("run_result", {})
    if not isinstance(run_result, dict):
        run_result = {}
    result_value = run_result.get("result")
    success = run_result.get("returncode") == 0 and result_value is not None
    old = candidate.get("objective_metrics", {})
    old = old if isinstance(old, dict) else {}
    runtime_s = to_numeric(candidate.get("runtime_s"))
    if runtime_s is None:
        runtime_s = to_numeric(run_result.get("duration_s"))
    if runtime_s is None:
        runtime_s = to_numeric(old.get("runtime_s")) or 0.0
    raw_calls = candidate.get("num_tool_calls")
    num_tool_calls = int(raw_calls) if isinstance(raw_calls, int) else 1
    if num_tool_calls < 0:
        num_tool_calls = 0
    pred_num = to_numeric(result_value) if gt_text else None
    abs_gap = (
        round(abs(pred_num - gt_num), 10) if pred_num is not None and gt_num is not None else None
    )
    return {
        "runtime_s": round(runtime_s, 3),
        "success": bool(success),
        "num_tool_calls": num_tool_calls,
        "abs_gap": abs_gap,
        "prediction_2dp": round_2dp_half_up(pred_num) if pred_num is not None else None,
        "ground_truth_2dp": round_2dp_half_up(gt_num) if gt_num is not None else None,
    }


# ---- shared row helpers ----------------------------------------------------


def norm_question(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def question_hash(text: str) -> str:
    return hashlib.sha256(norm_question(text).encode("utf-8")).hexdigest()[:16]


def row_candidates(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    rollout = row.get("rollout", {})
    cands = rollout.get("candidates", []) if isinstance(rollout, dict) else []
    return [c for c in cands if isinstance(c, dict)]


def row_index(row: Dict[str, Any]) -> Optional[int]:
    for key in ("index",):
        try:
            return int(row.get(key))
        except (TypeError, ValueError):
            continue
    m = re.match(r"sample_(\d+)$", str(row.get("sample_id", "")))
    return int(m.group(1)) if m else None


# ---- oracles ---------------------------------------------------------------


class LabelOracle:
    name = "base"

    def effective_gt(self, row: Dict[str, Any]) -> str:
        raise NotImplementedError

    def labels(self, row: Dict[str, Any]) -> List[str]:
        gt = self.effective_gt(row)
        return [host_label(c, gt) for c in row_candidates(row)]


class GTOracle(LabelOracle):
    """Vault judge: published labels as-is (D16), keyed by question hash."""

    name = "gt"

    def __init__(self, labels_path: str):
        self.by_hash: Dict[str, str] = {}
        with open(labels_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                q = rec.get("question")
                if q is None:
                    raise ValueError(
                        "labels file must carry question text per record "
                        "(point --labels at the ORIGINAL labeled jsonl)"
                    )
                self.by_hash[question_hash(str(q))] = str(rec.get("answer", ""))

    def effective_gt(self, row: Dict[str, Any]) -> str:
        h = question_hash(str(row.get("question", "")))
        if h not in self.by_hash:
            raise KeyError(
                f"no vault label for sample " f"{row.get('sample_id')} (question hash {h})"
            )
        return self.by_hash[h]


class RunsOKOracle(LabelOracle):
    """Host's native blind-mode judge: code ran => positive."""

    name = "runsok"

    def effective_gt(self, row: Dict[str, Any]) -> str:
        return ""


class VoteOracle(LabelOracle):
    """Majority vote over the sample's own successful candidates at 2dp.

    Majority = a unique modal 2dp value with count >= 2. No majority
    (all-distinct, all-failed, or tie) => NO_CONSENSUS sentinel: every
    candidate negative, sample ineligible.
    """

    name = "vote"

    def effective_gt(self, row: Dict[str, Any]) -> str:
        vals = []
        for c in row_candidates(row):
            if not candidate_success(c):
                continue
            v2 = round_2dp_half_up(to_numeric(candidate_result(c)))
            if v2 is not None:
                vals.append(v2)
        if not vals:
            return NO_CONSENSUS
        counts = Counter(vals).most_common()
        top_val, top_n = counts[0]
        if top_n < 2:
            return NO_CONSENSUS
        if len(counts) > 1 and counts[1][1] == top_n:
            return NO_CONSENSUS  # tie between modes
        return top_val


class GateOracle(LabelOracle):
    """AdmitOR certification judge.

    Reads one verdict json per sample from verdicts_dir, named
    <sample_id>.json (or <sample_key>.json), with at least:
        {"decision": "ACCEPT"|"ABSTAIN"|"UNINFORMATIVE"|"ESCALATE",
         "clique_value": <number or null>}
    ACCEPT  -> effective gt = clique value (candidates matching it positive)
    other   -> NO_CONSENSUS (nothing admitted without a certificate)
    missing -> recorded in self.work_order, treated as NO_CONSENSUS so a
               partial gate run never silently admits.
    """

    name = "gate"

    def __init__(self, verdicts_dir: str):
        self.verdicts_dir = verdicts_dir
        self.work_order: List[Dict[str, str]] = []

    def _verdict_path(self, row: Dict[str, Any]) -> Optional[str]:
        for key in ("sample_id", "sample_key"):
            name = str(row.get(key, "")).strip()
            if name:
                p = os.path.join(self.verdicts_dir, f"{name}.json")
                if os.path.isfile(p):
                    return p
        return None

    def effective_gt(self, row: Dict[str, Any]) -> str:
        path = self._verdict_path(row)
        if path is None:
            self.work_order.append(
                {
                    "sample_id": str(row.get("sample_id", "")),
                    "sample_key": str(row.get("sample_key", "")),
                    "question": str(row.get("question", "")),
                }
            )
            return NO_CONSENSUS
        with open(path, encoding="utf-8") as f:
            verdict = json.load(f)
        decision = str(verdict.get("decision", "")).upper()
        value = verdict.get("clique_value", verdict.get("answer_at_base_instance"))
        if decision == "ACCEPT" and value is not None:
            return str(value)
        return NO_CONSENSUS


def make_oracle(arm: str, labels_path: str = "", verdicts_dir: str = "") -> LabelOracle:
    arm = arm.lower()
    if arm == "gt":
        return GTOracle(labels_path)
    if arm == "vote":
        return VoteOracle()
    if arm == "runsok":
        return RunsOKOracle()
    if arm == "gate":
        return GateOracle(verdicts_dir)
    raise ValueError(f"unknown arm: {arm}")
