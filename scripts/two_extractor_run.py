# -*- coding: utf-8 -*-
"""Two-extractor preliminary: run the unchanged extraction prompt on two further families.

Calls `admitor.ir_extract.extract_spec` with a closure routed to each family,
so the prompt, the JSON parsing and the `validate_spec` guardrails are
identical to the pilot. Records request parameters, resp_model and usage per
call. This is the only script of the reviewer round that calls a model
(88 calls: 44 cases x 2 families).

Inputs
    --family     model name as served by the endpoint (claude-sonnet-4-6, gpt-5.4)
    --cases      release/reviewer_round/09_cases.csv (in git)
    --workorder  <host>/outputs/e1/gate_workorder.jsonl, the problem text
                 (private, not distributed)
    --out        default reanalysis/reviewer_round/09_extractions
    credentials  OPTSKILL_BASE_URL and OPTSKILL_API_KEY from the environment,
                 or from the file passed as --env-file (private, not distributed)

Input availability key: "in git" = shipped in this repository; "release
asset" = the v1.0.0 GitHub release asset admitor-v1.0.0-runlogs.zip; "private,
not distributed" = kept by the authors (<host> below is the OptSkills host
clone the experiments ran in).

This script is not runnable from the public checkout alone: it needs an API
key and the private workorder.

Reproduce (from the repository root)
    python scripts/two_extractor_run.py --family claude-sonnet-4-6 --workorder <host>/outputs/e1/gate_workorder.jsonl
    python scripts/two_extractor_run.py --family gpt-5.4 --workorder <host>/outputs/e1/gate_workorder.jsonl

Outputs
    <out>/<family>/<sample_id>.json, <out>/ledger_<family>.csv

Paper location
    Section 4.3 (22/22, 21/22 vs 18/22) and Appendix B.1 Table 4.
"""
from __future__ import annotations
import argparse, csv, json, os, sys, threading, time, urllib.error, urllib.request
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))  # repository root
from admitor.ir_extract import extract_spec

BASE = (os.environ.get("OPTSKILL_BASE_URL") or "").rstrip("/") or None
KEY = os.environ.get("OPTSKILL_API_KEY") or None


def load_env_file(path):
    global BASE, KEY
    for line in open(path, encoding="utf-8"):
        s = line.strip()
        if s.startswith("OPTSKILL_BASE_URL="):
            BASE = s.split("=", 1)[1].strip().strip('"').strip("'").rstrip("/")
        if s.startswith("OPTSKILL_API_KEY="):
            KEY = s.split("=", 1)[1].strip().strip('"').strip("'")

LOCK = threading.Lock()
LEDGER = []


def make_call(model, sid):
    def f(prompt):
        p = {"model": model, "temperature": 0, "max_tokens": 8192,
             "messages": [{"role": "user", "content": prompt}]}
        req = urllib.request.Request(BASE + "/chat/completions", method="POST")
        req.add_header("Authorization", "Bearer " + KEY)
        req.add_header("Content-Type", "application/json")
        last = None
        for attempt in range(3):
            t0 = time.time()
            try:
                with urllib.request.urlopen(req, json.dumps(p).encode(), timeout=300) as z:
                    b = json.loads(z.read().decode())
                u = b.get("usage") or {}
                with LOCK:
                    LEDGER.append(dict(sample_id=sid, requested=model,
                                       resp_model=b.get("model"),
                                       prompt_tokens=u.get("prompt_tokens"),
                                       completion_tokens=u.get("completion_tokens"),
                                       total_tokens=u.get("total_tokens"),
                                       latency_s=round(time.time() - t0, 2),
                                       attempt=attempt, error=""))
                return b["choices"][0]["message"].get("content") or ""
            except Exception as e:
                last = "%s: %s" % (type(e).__name__, e)
                time.sleep(2 * (attempt + 1))
        with LOCK:
            LEDGER.append(dict(sample_id=sid, requested=model, resp_model="",
                               prompt_tokens=None, completion_tokens=None,
                               total_tokens=None, latency_s=None, attempt=3,
                               error=last))
        raise RuntimeError(last)
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True)
    ap.add_argument("--cases", default="release/reviewer_round/09_cases.csv")
    ap.add_argument("--workorder", required=True)
    ap.add_argument("--env-file", default="")
    ap.add_argument("--out", default="reanalysis/reviewer_round/09_extractions")
    ap.add_argument("--workers", type=int, default=3)
    a = ap.parse_args()
    if a.env_file:
        load_env_file(a.env_file)
    d = os.path.join(a.out, a.family)
    os.makedirs(d, exist_ok=True)

    wo = a.workorder
    q = {}
    for line in open(wo, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            q[str(r.get("sample_id"))] = r.get("question", "")

    cases = list(csv.DictReader(open(a.cases, encoding="utf-8")))
    todo = [c for c in cases if not os.path.isfile(os.path.join(d, c["sample_id"] + ".json"))]
    print("family %s: %d cases, %d to run" % (a.family, len(cases), len(todo)), flush=True)

    def work(c):
        sid = c["sample_id"]
        try:
            res = extract_spec(q.get(sid, ""), make_call(a.family, sid))
            doc = dict(sample_id=sid, family=a.family, group=c["group"],
                       k3_class=c["k3_class"], score=c["score"],
                       spec=res["spec"], sense=res.get("sense"),
                       warnings=res.get("warnings"), raw=res.get("raw"))
        except Exception as e:
            doc = dict(sample_id=sid, family=a.family, group=c["group"],
                       k3_class=c["k3_class"], score=c["score"],
                       error="%s: %s" % (type(e).__name__, e))
        with open(os.path.join(d, sid + ".json"), "w", encoding="utf-8", newline="\n") as fh:
            json.dump(doc, fh, ensure_ascii=False, indent=1)
        print("  %s %s %s" % (a.family, sid, "ERROR" if "error" in doc else "ok"), flush=True)

    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        list(pool.map(work, todo))

    lp = os.path.join(a.out, "ledger_%s.csv" % a.family)
    if LEDGER:
        with open(lp, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=list(LEDGER[0].keys()))
            w.writeheader(); w.writerows(LEDGER)
    tot = sum(x.get("total_tokens") or 0 for x in LEDGER)
    print("calls %d, total tokens %d, ledger %s" % (len(LEDGER), tot, lp))
    return 0


if __name__ == "__main__":
    sys.exit(main())
