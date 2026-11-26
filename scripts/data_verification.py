# -*- coding: utf-8 -*-
"""Data verification: each model family checks the extracted parameters against the problem text.

Purpose
    For every problem of a certification run and every requested family, send one request with the
    problem text and the extracted parameter set (name | meaning | base value), and store the reply.
    A family reports, per parameter, a `mismatch` (the text gives another value, order or entity) and
    `not_stated` (the text does not give the value). The stored record carries `flag_mismatch`,
    `flag_not_stated` and `flag_any`. A reply that cannot be parsed into the two lists is requested again
    with the identical prompt, model and settings, up to three attempts in total (recorded in "attempts");
    only if all three fail does the record keep status "unparsed" and no flags. An API failure has status
    "api_error". The certificate rule "B or C" withdraws a certificate when family
    B or family C raises flag_any.

Inputs
    --runs        a certification runs directory (one folder per problem with spec.json), e.g.
                  the output of scripts/e1_certify.py --runs-dir, or artifacts/v2/<set>/runs
    --work-order  JSONL with {"sample_id", "question"} per problem (the problem text given to the models)
    --out         output directory
    --families    families to query (default ABC)
    --only        optional file with one problem id per line (default: every problem with a spec.json)
    --workers     concurrent requests per family (default 4)
    Environment, per family X in A, B, C: ADMITOR_API_KEY_X, ADMITOR_BASE_URL_X, ADMITOR_MODEL_X, and
    optionally ADMITOR_EXTRA_JSON_X (a JSON object passed as extra request body), the same variables
    that certification uses. Requests use temperature 0 and max_tokens 8192.

Outputs
    <out>/<problem id>/verification_<X>.json   one record per problem and family
    <out>/usage.jsonl                          token usage per request
    A problem and family whose record already has status "ok" or "unparsed" is skipped, so a run
    can be resumed; with --retry-unparsed a stored "unparsed" record with fewer than three attempts is
    requested again (the stored reply counts as attempt 1).

Usage (from the repository root)
    python scripts/data_verification.py --runs <runs dir> --work-order <problem file> --out <dir>
"""
import argparse
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

PROMPT = (
    "You are checking a data extraction. Below are an optimization problem statement and the parameter values that were "
    "extracted from it. For every parameter, compare its value with the statement and report two kinds of problems.\n"
    "(1) mismatch: the statement gives a different number, a different order of the entries, or assigns the value to a "
    "different entity.\n"
    "(2) not_stated: the statement does not give the value. This includes values for which the statement gives only "
    "examples, only a range, or says that similar values apply, and values that were filled in to complete a table.\n"
    "Do not judge modeling choices. Do not report index sets, counts or constants that follow directly from the statement. "
    "Return JSON only, in the form {\"mismatch\": [{\"parameter\": \"<name>\", \"extracted\": <value>, \"stated\": <value>, "
    "\"evidence\": \"<short quote>\"}], \"not_stated\": [{\"parameter\": \"<name>\", \"evidence\": \"<short quote or 'no "
    "value in the statement'>\"}]}. If there is no problem, return {\"mismatch\": [], \"not_stated\": []}.\n\n"
    "STATEMENT:\n%s\n\nPARAMETERS:\n%s")


def parameters(run_dir):
    sp = json.load(open(os.path.join(run_dir, "spec.json"), encoding="utf-8"))
    rawp = (sp.get("raw") or {}).get("params") or {}
    lines = []
    for n, v in (sp.get("spec") or {}).items():
        meaning = (rawp.get(n) or {}).get("meaning") or ""
        lines.append("%s | %s | %s" % (n, meaning, json.dumps(v.get("base"), ensure_ascii=False, separators=(",", ":"))))
    return "\n".join(lines)


def parse(text):
    t = (text or "").strip()
    m = re.search(r"```(?:json)?\s*(.*?)```", t, re.S)
    cands = [t] + ([m.group(1)] if m else [])
    if "{" in t and "}" in t:
        cands.append(t[t.index("{"):t.rindex("}") + 1])
    for c in cands:
        try:
            d = json.loads(c)
        except ValueError:
            continue
        if isinstance(d, dict) and any(k in d for k in ("mismatch", "not_stated")):
            mm, ns = d.get("mismatch", []), d.get("not_stated", [])
            if isinstance(mm, list) and isinstance(ns, list):
                return d, [k for k in ("mismatch", "not_stated") if k not in d]
    return None, None


ATTEMPTS = 3  # a reply that cannot be parsed is requested again, identically, up to three attempts in total


def stored(path):
    if not os.path.isfile(path):
        return None
    try:
        return json.load(open(path, encoding="utf-8"))
    except ValueError:
        return None


def done(path, retry_unparsed=False):
    r = stored(path)
    if r is None:
        return False
    if r.get("status") == "ok":
        return True
    if r.get("status") == "unparsed":
        return not retry_unparsed or len(r.get("attempts") or [{}]) >= ATTEMPTS
    return False


def main():
    ap = argparse.ArgumentParser(description="Data verification of extracted parameters by each model family.")
    ap.add_argument("--runs", required=True)
    ap.add_argument("--work-order", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--families", default="ABC")
    ap.add_argument("--only", default="")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--retry-unparsed", action="store_true",
                    help="request again a stored reply with status unparsed (the stored reply counts as attempt 1)")
    a = ap.parse_args()
    fams = [f for f in a.families if f in "ABC"]
    for f in fams:
        for var in ("ADMITOR_API_KEY_", "ADMITOR_BASE_URL_", "ADMITOR_MODEL_"):
            if not os.environ.get(var + f):
                sys.exit("data_verification.py: environment variable %s%s is not set" % (var, f))
    from openai import OpenAI  # OpenAI-compatible client, also used by certification

    models = {f: os.environ["ADMITOR_MODEL_" + f] for f in fams}
    clients = {f: OpenAI(api_key=os.environ["ADMITOR_API_KEY_" + f], base_url=os.environ["ADMITOR_BASE_URL_" + f]) for f in fams}
    extra = {f: (json.loads(os.environ["ADMITOR_EXTRA_JSON_" + f]) if os.environ.get("ADMITOR_EXTRA_JSON_" + f) else None) for f in fams}
    q = {}
    for l in open(a.work_order, encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            q[r["sample_id"]] = r["question"]
    ids = sorted(s for s in os.listdir(a.runs) if os.path.isfile(os.path.join(a.runs, s, "spec.json")))
    if a.only:
        keep = {l.strip() for l in open(a.only, encoding="utf-8") if l.strip()}
        ids = [s for s in ids if s in keep]
    missing = [s for s in ids if s not in q]
    if missing:
        sys.exit("data_verification.py: %d problems have no question in the problem file, e.g. %s" % (len(missing), missing[0]))
    os.makedirs(a.out, exist_ok=True)
    usage = os.path.join(a.out, "usage.jsonl")
    lock = threading.Lock()

    def request(fam, prompt, kw):
        r, err, t0 = None, None, time.time()
        for wait in (0, 5, 15, 30, 60, 120):
            time.sleep(wait)
            try:
                t0 = time.time()
                r = clients[fam].chat.completions.create(model=models[fam], temperature=0, max_tokens=8192,
                                                         messages=[{"role": "user", "content": prompt}], **kw)
                return r, None, t0
            except Exception as e:  # retried, then recorded as api_error, never as a flag
                err = "%s: %s" % (type(e).__name__, str(e)[:300])
        return None, err, t0

    def task(sid, fam):
        path = os.path.join(a.out, sid, "verification_%s.json" % fam)
        if done(path, a.retry_unparsed):
            return
        prev = stored(path)
        attempts = []
        if prev and prev.get("status") == "unparsed":  # a stored unparsed reply counts as an attempt
            attempts = prev.get("attempts") or [{"attempt": 1, "status": "unparsed",
                                                 "finish_reason": prev.get("finish_reason"), "reply": prev.get("reply", "")}]
        prompt = PROMPT % (q[sid], parameters(os.path.join(a.runs, sid)))
        kw = {"extra_body": extra[fam]} if extra[fam] else {}
        os.makedirs(os.path.dirname(path), exist_ok=True)
        rec = None
        while len(attempts) < ATTEMPTS:
            r, err, t0 = request(fam, prompt, kw)
            if r is None:
                json.dump({"sample_id": sid, "family": fam, "model": models[fam], "status": "api_error", "error": err,
                           "attempts": attempts}, open(path, "w", encoding="utf-8"), indent=1)
                return
            u = r.usage.model_dump() if getattr(r, "usage", None) else {}
            reply = r.choices[0].message.content or ""
            with lock:
                with open(usage, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"sample_id": sid, "family": fam, "requested": models[fam],
                                         "response_model": getattr(r, "model", None), "usage": u,
                                         "seconds": round(time.time() - t0, 2)}) + "\n")
            d, miss = parse(reply)
            att = {"attempt": len(attempts) + 1, "status": "ok" if d is not None else "unparsed",
                   "finish_reason": r.choices[0].finish_reason}
            if d is None:
                att["reply"] = reply
            attempts.append(att)
            rec = {"sample_id": sid, "family": fam, "model": models[fam], "response_model": getattr(r, "model", None),
                   "finish_reason": r.choices[0].finish_reason, "status": "ok" if d is not None else "unparsed", "reply": reply}
            if d is not None:
                rec.update(mismatch=d.get("mismatch", []), not_stated=d.get("not_stated", []), missing_keys=miss,
                           flag_mismatch=bool(d.get("mismatch")), flag_not_stated=bool(d.get("not_stated")))
                rec["flag_any"] = rec["flag_mismatch"] or rec["flag_not_stated"]
                break
        if rec is None:  # all attempts were stored before; nothing to request
            return
        rec["attempts"] = attempts
        json.dump(rec, open(path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

    pools = {f: ThreadPoolExecutor(max_workers=a.workers) for f in fams}
    futs = [pools[f].submit(task, s, f) for f in fams for s in ids]
    for x in futs:
        x.result()
    print(json.dumps({"problems": len(ids), "families": "".join(fams), "out": a.out}))


if __name__ == "__main__":
    main()
