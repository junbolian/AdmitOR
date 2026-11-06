# -*- coding: utf-8 -*-
"""Single-model LLM judge as an admission rule for host trajectories.

Purpose
    A simpler verification strategy: one strong model reads the problem text
    and a host trajectory's program with its returned value, and answers
    CORRECT or INCORRECT. A trajectory is admitted when the answer is
    CORRECT. The result is scored at the candidate level exactly like the
    rows of the judge tables: admitted trajectories, wrong admissions,
    precision, and recall over the correct trajectories.

Model calls
    One call per judged trajectory, temperature 0, through an
    OpenAI-compatible chat endpoint. Settings come from the environment:
        JUDGE_BASE_URL   e.g. the relay base URL ending in /v1
        JUDGE_API_KEY    never printed or written
        JUDGE_MODEL      e.g. claude-sonnet-4-6
    Every response is appended to <out>/llm_judge_cache.jsonl keyed by the
    trajectory key, so an interrupted run resumes without paying twice. The
    response-side model name is stored with every record.

Inputs
    --collect   the host collect file (one problem per line, with its rollouts)
    --vault     datasets/vault/optmath-train-300-labels.jsonl
    Field paths in the collect file are given by flags (dotted paths), found
    with --peek:
        --id-key        problem id field of a line, e.g. sample_id
        --question-key  problem text field of a line
        --traj-key      list of rollouts inside a line
        --code-key      program text inside a rollout
        --value-key     returned objective value inside a rollout (None when
                        the run failed)

Reconciliation gate (before any model call)
    Over non-dev problems, the rollouts with a returned value must number 878
    and 637 of them must match the label under the host's equality rule
    (round half-up to 2 decimals, or absolute gap <= 0.005). These are the
    execution-success arm's 878 admissions with 241 wrong. Any difference
    prints STOP and exits with code 2.

Usage
    python scripts/llm_judge.py --collect <file> --peek
    python scripts/llm_judge.py --collect <file> <field flags> --gate-only
    python scripts/llm_judge.py --collect <file> <field flags> --limit 20
    python scripts/llm_judge.py --collect <file> <field flags>

Outputs
    <out>/llm_judge_cache.jsonl, <out>/llm_judge_row.md, <out>/llm_judge_row.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.request
from decimal import Decimal, ROUND_HALF_UP

DEV = {"sample_%d" % i for i in (1, 2, 3, 4, 5)}

PROMPT = """You are given an optimization problem stated in natural language and a Python program that a modeling agent wrote to solve it, together with the optimal objective value the program returned.

Decide whether the program is a correct model of the problem: the decision variables, the objective, every constraint and every data value must match the problem statement.

Problem:
<<<
{question}
>>>

Program:
<<<
{code}
>>>

Returned optimal objective value: {value}

Answer with one JSON object and nothing else:
{{"verdict": "CORRECT" or "INCORRECT", "reason": "<one sentence>"}}"""


def get(obj, path):
    for part in path.split("."):
        if obj is None:
            return None
        if isinstance(obj, list):
            obj = obj[int(part)] if part.isdigit() and int(part) < len(obj) else None
        else:
            obj = obj.get(part)
    return obj


def num(x):
    try:
        v = float(x)
        return v if v == v and abs(v) != float("inf") else None
    except (TypeError, ValueError):
        return None


def host_equal(pred, label):
    p, g = num(pred), num(label)
    if p is None or g is None:
        return False
    q = lambda v: Decimal(repr(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return q(p) == q(g) or abs(p - g) <= 0.005


def peek(path):
    line = next(l for l in open(path, encoding="utf-8") if l.strip())
    doc = json.loads(line)

    def walk(o, pre, depth):
        if depth > 4:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                kind = type(v).__name__
                sample = repr(v)[:70] if not isinstance(v, (dict, list)) else ""
                print("%s%s  (%s) %s" % ("  " * depth, pre + k, kind, sample))
                walk(v, pre + k + ".", depth + 1)
        elif isinstance(o, list) and o:
            print("%s%s[0..%d]" % ("  " * depth, pre, len(o) - 1))
            walk(o[0], pre + "0.", depth + 1)
    walk(doc, "", 0)


def call(prompt):
    body = json.dumps({"model": os.environ["JUDGE_MODEL"], "temperature": 0, "max_tokens": 300,
                       "messages": [{"role": "user", "content": prompt}]}).encode("utf-8")
    req = urllib.request.Request(os.environ["JUDGE_BASE_URL"].rstrip("/") + "/chat/completions", data=body,
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ["JUDGE_API_KEY"]})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # transient network errors: retry with backoff
            if attempt == 3:
                raise
            time.sleep(5 * (attempt + 1))


def parse(text):
    m = re.search(r"\{.*\}", text or "", re.S)
    if m:
        try:
            v = json.loads(m.group(0)).get("verdict", "")
            if v in ("CORRECT", "INCORRECT"):
                return v
        except json.JSONDecodeError:
            pass
    return "UNPARSEABLE"


def main():
    ap = argparse.ArgumentParser(description="Single-model LLM judge as an admission rule.")
    ap.add_argument("--collect", required=True)
    ap.add_argument("--vault", default="datasets/vault/optmath-train-300-labels.jsonl")
    ap.add_argument("--out", default="outputs/additional_2026-11b")
    ap.add_argument("--peek", action="store_true")
    ap.add_argument("--gate-only", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--id-key", default="sample_id")
    ap.add_argument("--question-key", default="question")
    ap.add_argument("--traj-key", default="trajectories")
    ap.add_argument("--code-key", default="code")
    ap.add_argument("--value-key", default="objective")
    a = ap.parse_args()
    if a.peek:
        peek(a.collect); return

    vault = {}
    for line in open(a.vault, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            vault["sample_%s" % r["idx"]] = str(r.get("answer"))

    items = []  # (key, sid, question, code, value, correct)
    for line in open(a.collect, encoding="utf-8"):
        if not line.strip():
            continue
        doc = json.loads(line)
        sid = str(get(doc, a.id_key))
        if not sid.startswith("sample_"):
            sid = "sample_%s" % sid
        if sid in DEV or sid not in vault:
            continue
        for t, tr in enumerate(get(doc, a.traj_key) or []):
            raw = get(tr, a.value_key)
            if get(tr, "run_result.returncode") != 0 or raw is None:   # host success rule
                continue
            val = num(raw) if num(raw) is not None else raw            # a dict result is kept as-is
            items.append(("%s#%d" % (sid, t), sid, get(doc, a.question_key), get(tr, a.code_key), val,
                          host_equal(raw, vault[sid])))
    n_ok, n_right = len(items), sum(1 for it in items if it[5])
    print("rollouts with a value (non-dev): %d, matching the label: %d" % (n_ok, n_right))
    if (n_ok, n_right) != (878, 637):
        print("STOP: expected 878 and 637 (execution-success arm 878 admitted, 241 wrong)"); sys.exit(2)
    if any(not it[2] or not it[3] for it in items):
        print("STOP: some rollouts lack a problem text or a program; check --question-key/--code-key"); sys.exit(2)
    print("RECONCILIATION PASSED")
    if a.gate_only:
        return

    os.makedirs(a.out, exist_ok=True)
    cache_path = os.path.join(a.out, "llm_judge_cache.jsonl")
    cache = {}
    if os.path.isfile(cache_path):
        for line in open(cache_path, encoding="utf-8"):
            if line.strip():
                r = json.loads(line)
                cache[r["key"]] = r
    todo = [it for it in items if it[0] not in cache]
    if a.limit:
        todo = todo[: a.limit]
    with open(cache_path, "a", encoding="utf-8") as fh:
        for i, (key, sid, q, code, val, _) in enumerate(todo, 1):
            resp = call(PROMPT.format(question=q, code=code, value=val))
            text = resp["choices"][0]["message"].get("content", "")
            rec = {"key": key, "sample_id": sid, "verdict": parse(text), "raw": text,
                   "resp_model": resp.get("model"), "usage": resp.get("usage")}
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n"); fh.flush()
            cache[key] = rec
            if i % 50 == 0:
                print("judged %d of %d" % (i, len(todo)))

    judged = [it for it in items if it[0] in cache]
    adm = [it for it in judged if cache[it[0]]["verdict"] == "CORRECT"]
    wrong = sum(1 for it in adm if not it[5])
    unp = sum(1 for it in judged if cache[it[0]]["verdict"] == "UNPARSEABLE")
    usage_in = sum((cache[it[0]].get("usage") or {}).get("prompt_tokens", 0) for it in judged)
    usage_out = sum((cache[it[0]].get("usage") or {}).get("completion_tokens", 0) for it in judged)
    models = sorted({str(cache[it[0]].get("resp_model")) for it in judged})
    prec = (len(adm) - wrong) / len(adm) if adm else float("nan")
    rec_ = (len(adm) - wrong) / 637
    row = dict(judge="llm_judge_" + os.environ.get("JUDGE_MODEL", "model"), judged=len(judged),
               admitted=len(adm), wrong=wrong, precision=round(prec, 4), recall=round(rec_, 4),
               unparseable=unp, prompt_tokens=usage_in, completion_tokens=usage_out,
               response_models=";".join(models))
    with open(os.path.join(a.out, "llm_judge_row.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row)); w.writeheader(); w.writerow(row)
    md = ["| " + " | ".join(row) + " |", "|" + "---|" * len(row), "| " + " | ".join(str(v) for v in row.values()) + " |"]
    open(os.path.join(a.out, "llm_judge_row.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))
    if len(judged) < len(items):
        print("PARTIAL: %d of %d rollouts judged; the row is not final" % (len(judged), len(items)))


if __name__ == "__main__":
    main()
