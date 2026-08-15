# -*- coding: utf-8 -*-
"""E1 oracle tests against the real collect schema.

Checkpoints, keeping the labels used during development:
  T1  the port of the host's judging semantics (2dp HALF_UP equality with an
      abs-gap fallback, blind-mode success-equals-positive) matches the host.
  T2  VoteOracle over majority, all-distinct, all-failed and tie rows.
  T3  RunsOKOracle, the host's native blind-mode judge.
  T4  GTOracle keyed by normalized question hash, and its loud failure on a
      missing label.
  T5  GateOracle over accept, abstain, and a missing verdict routed to the
      work order.
  T6  e1_relabel.py end to end on a mini collect file, all four arms.
  T7  the metrics rewrite, which is the trap that silently degrades every arm
      to runs-ok semantics if the stored objective_metrics are left stale.

Runs fully offline. T6 spawns e1_relabel.py as a subprocess inside a tmp
directory; nothing reaches the network and no credentials are read.
"""
import json
import os
import subprocess
import sys

from label_oracle import (
    NO_CONSENSUS,
    GateOracle,
    GTOracle,
    RunsOKOracle,
    VoteOracle,
    attach_metrics,
    host_label,
    round_2dp_half_up,
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELABEL = os.path.join(REPO_ROOT, "scripts", "e1_relabel.py")


def cand(cid, result, rc=0):
    return {
        "candidate_id": cid,
        "solver_id": "s",
        "family": "keyword_slots",
        "run_result": {"returncode": rc, "result": result},
    }


def row(idx, question, cands):
    return {
        "phase": "cluster",
        "index": idx,
        "sample_key": str(idx),
        "sample_id": f"sample_{idx}",
        "question": question,
        "answer": "",
        "rollout": {"selection": {}, "candidates": cands},
        "eligible": True,
    }


# rows: r1 majority 10/10/7 ; r2 all distinct ; r3 all failed ; r4 tie 2-2
R1 = row(6, "q six", [cand("a", 10.0), cand("b", 10.001), cand("c", 7.0)])
R2 = row(7, "q seven", [cand("a", 1.0), cand("b", 2.0), cand("c", 3.0)])
R3 = row(8, "q eight", [cand("a", None), cand("b", 4.0, rc=1)])
R4 = row(9, "q nine", [cand("a", 5.0), cand("b", 5.0), cand("c", 6.0), cand("d", 6.0)])


def test_t1_host_semantics_port():
    """T1: the host judging semantics port."""
    assert round_2dp_half_up(2.675) == "2.68"  # HALF_UP via str()
    assert host_label(cand("x", 7337.0), "7337") == "positive"
    assert host_label(cand("x", 7337.004), "7337") == "positive"  # 2dp equal
    assert host_label(cand("x", 7337.006), "7337") == "negative"
    assert host_label(cand("x", None), "7337") == "negative"
    assert host_label(cand("x", 5.0, rc=1), "5") == "negative"
    assert host_label(cand("x", 123.0), "") == "positive"  # blind mode


def test_t2_vote_oracle():
    """T2: majority, all-distinct, all-failed and tie."""
    v = VoteOracle()
    assert v.effective_gt(R1) == "10.00"
    assert v.labels(R1) == ["positive", "positive", "negative"]
    assert v.effective_gt(R2) == NO_CONSENSUS
    assert set(v.labels(R2)) == {"negative"}
    assert v.effective_gt(R3) == NO_CONSENSUS
    assert v.effective_gt(R4) == NO_CONSENSUS  # tie between modes


def test_t3_runsok_oracle():
    """T3: code-ran-equals-positive."""
    ro = RunsOKOracle()
    assert ro.labels(R2) == ["positive", "positive", "positive"]
    assert ro.labels(R3) == ["negative", "negative"]


def _write_labels(tmp_path):
    p = tmp_path / "labels.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        f.write(json.dumps({"index": 6, "question": "q   SIX", "answer": "10"}) + "\n")
        f.write(json.dumps({"index": 7, "question": "q seven", "answer": "2"}) + "\n")
    return p


def test_t4_gt_oracle(tmp_path):
    """T4: hash match plus a loud miss."""
    g = GTOracle(str(_write_labels(tmp_path)))
    # whitespace and case normalized before hashing
    assert g.effective_gt(R1) == "10"
    assert g.labels(R2) == ["negative", "positive", "negative"]
    try:
        g.effective_gt(R3)
    except KeyError:
        pass
    else:
        raise AssertionError("a missing vault label must raise KeyError")


def _write_verdicts(tmp_path):
    d = tmp_path / "verdicts"
    d.mkdir(exist_ok=True)
    json.dump(
        {"decision": "ACCEPT", "clique_value": 10.0},
        open(d / "sample_6.json", "w", encoding="utf-8"),
    )
    json.dump(
        {"decision": "ABSTAIN", "clique_value": None},
        open(d / "sample_7.json", "w", encoding="utf-8"),
    )
    return d


def test_t5_gate_oracle(tmp_path):
    """T5: accept, abstain, and missing routed to the work order."""
    ga = GateOracle(str(_write_verdicts(tmp_path)))
    assert ga.effective_gt(R1) == "10.0"
    assert ga.labels(R1) == ["positive", "positive", "negative"]
    assert ga.effective_gt(R2) == NO_CONSENSUS
    assert ga.effective_gt(R3) == NO_CONSENSUS
    assert len(ga.work_order) == 1
    assert ga.work_order[0]["sample_id"] == "sample_8"


def test_t6_e1_relabel_end_to_end(tmp_path):
    """T6: all four arms through the driver; gt fails loud on a missing
    label."""
    labels = _write_labels(tmp_path)
    verdicts = _write_verdicts(tmp_path)
    collect = tmp_path / "mini_collect.jsonl"
    with open(collect, "w", encoding="utf-8") as f:
        for r in (R1, R2, R3):
            f.write(json.dumps(r) + "\n")

    def run(args, expect_ok=True):
        out = subprocess.run(
            [sys.executable, RELABEL] + args, capture_output=True, text=True, cwd=str(tmp_path)
        )
        if expect_ok:
            assert out.returncode == 0, out.stderr
        return out

    run(["--collect", str(collect), "--arm", "vote", "--out", "out/vote.jsonl"])
    run(["--collect", str(collect), "--arm", "runsok", "--out", "out/runsok.jsonl"])
    # R3 carries no vault label, so the gt arm must fail loudly rather than
    # silently relabel it.
    p = run(
        [
            "--collect",
            str(collect),
            "--arm",
            "gt",
            "--labels",
            str(labels),
            "--out",
            "out/gt.jsonl",
        ],
        expect_ok=False,
    )
    assert p.returncode != 0
    assert "no vault label" in (p.stderr or "")
    run(
        [
            "--collect",
            str(collect),
            "--arm",
            "gate",
            "--verdicts-dir",
            str(verdicts),
            "--out",
            "out/gate.jsonl",
            "--work-order",
            "out/gate_workorder.jsonl",
        ]
    )

    vrows = [json.loads(l) for l in open(tmp_path / "out" / "vote.jsonl", encoding="utf-8")]
    assert vrows[0]["answer"] == "10.00" and vrows[0]["eligible"] is True
    assert vrows[1]["answer"] == NO_CONSENSUS and vrows[1]["eligible"] is False
    assert vrows[0]["e1_arm"] == "vote"
    assert vrows[0]["e1_original_answer"] == ""

    wo = [json.loads(l) for l in open(tmp_path / "out" / "gate_workorder.jsonl", encoding="utf-8")]
    assert len(wo) == 1 and wo[0]["sample_id"] == "sample_8"
    s = json.load(open(tmp_path / "out" / "gate.jsonl.summary.json", encoding="utf-8"))
    assert s["missing_certifications"] == 1


def test_t7_metrics_rewrite(tmp_path):
    """T7: stale blind metrics are replaced and the sentinel stays numeric."""
    c_stale = cand("a", 7.0)
    c_stale["objective_metrics"] = {
        "runtime_s": 0.2,
        "success": True,
        "num_tool_calls": 3,
        "abs_gap": None,
        "prediction_2dp": None,
        "ground_truth_2dp": None,
    }
    m = attach_metrics(c_stale, "10.00")
    assert m["success"] is True and m["prediction_2dp"] == "7.00"
    assert m["ground_truth_2dp"] == "10.00" and m["abs_gap"] == 3.0
    # host semantics: a non-int raw num_tool_calls becomes 1
    assert m["num_tool_calls"] == 1
    m_blind = attach_metrics(c_stale, "")
    assert m_blind["prediction_2dp"] is None
    assert m_blind["ground_truth_2dp"] is None

    # the driver writes the rewritten metrics into its output rows
    collect = tmp_path / "mini_collect.jsonl"
    with open(collect, "w", encoding="utf-8") as f:
        for r in (R1, R2, R3):
            f.write(json.dumps(r) + "\n")
    out = subprocess.run(
        [
            sys.executable,
            RELABEL,
            "--collect",
            str(collect),
            "--arm",
            "vote",
            "--out",
            "out/vote.jsonl",
        ],
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
    )
    assert out.returncode == 0, out.stderr
    vr = [json.loads(l) for l in open(tmp_path / "out" / "vote.jsonl", encoding="utf-8")]
    mc = vr[0]["rollout"]["candidates"][2]["objective_metrics"]  # the 7.0 one
    assert mc["ground_truth_2dp"] == "10.00" and mc["prediction_2dp"] == "7.00"
    mc_nc = vr[1]["rollout"]["candidates"][0]["objective_metrics"]
    assert mc_nc["ground_truth_2dp"] is None
    assert mc_nc["abs_gap"] is not None
    # the NO_CONSENSUS sentinel routes through abs_gap and stays negative
    assert mc_nc["abs_gap"] > 1e300
