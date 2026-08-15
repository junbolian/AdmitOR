# -*- coding: utf-8 -*-
"""AdmitOR runlog v0 -- the logging substrate (a first-class component).

Purpose
    Capture every LLM call and every solver call into a JSONL ledger,
    content-addressed. Design principle: do not modify host (OptSkills)
    logic, only wrap a layer around the point where the client is
    instantiated.

Inputs
    Calls made by the instrumented code path. Nothing is read from disk.

Outputs
    One JSONL file, one record per line. Every record carries ts, run_id and
    operator, plus the fields of its own record kind:
        kind "llm"    model, family, strategy, prompt_hash, request_meta,
                      response_hash, response_chars, usage, latency_s, tags
        kind "solve"  solver, status, objective, solve_time_s, params_hash,
                      code_hash, binding, extra
    Prompt and response bodies are never written, only their sha256 content
    addresses and sizes, so the ledger can be published without leaking
    problem text or model output.

Usage (LLM side, any OpenAI-compatible client)
    from runlog import RunLogger, wrap_openai_client
    logger = RunLogger("runs/e0_os.jsonl", run_id="e0-os-001", operator="ci")
    client = wrap_openai_client(OpenAI(api_key=..., base_url=...), logger,
                                family="deepseek", strategy="host")
    # client.chat.completions.create(...) is then used as normal and is
    # recorded automatically.

Usage (solver side)
    from runlog import log_solve
    log_solve(logger, solver="highs",
              status=str(res.solver.termination_condition),
              objective=val, solve_time=t, params_hash=h, extra={...})

Example invocation (self-test, writes runs/selftest.jsonl)
    python scripts/runlog.py
"""
import hashlib
import json
import os
import threading
import time
import uuid


def content_hash(obj) -> str:
    """Deterministic content address: sha256 of any JSON-serializable object,
    truncated to the leading 16 hex characters."""
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()[:16]


class RunLogger:
    """Thread-safe append-only JSONL log. One record per line; the record
    schema is the one specified in protocol v2.0 section 3."""

    def __init__(self, path: str, run_id: str = None, operator: str = "unknown"):
        self.path = path
        self.run_id = run_id or ("run-" + uuid.uuid4().hex[:8])
        self.operator = operator
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def write(self, record: dict):
        base = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "run_id": self.run_id,
            "operator": self.operator,
        }
        base.update(record)
        line = json.dumps(base, ensure_ascii=False, default=str)
        with self._lock:
            with open(self.path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

    # ---- convenience methods ----
    def log_llm(
        self,
        *,
        model,
        family,
        strategy,
        request,
        response_text,
        usage=None,
        latency_s=None,
        tags=None,
    ):
        self.write(
            {
                "kind": "llm",
                "model": model,
                "family": family,
                "strategy": strategy,
                "prompt_hash": content_hash(request),
                "request_meta": {
                    k: request.get(k)
                    for k in ("model", "temperature", "max_tokens", "seed")
                    if k in request
                },
                "response_hash": content_hash(response_text),
                "response_chars": len(response_text or ""),
                "usage": usage or {},
                "latency_s": latency_s,
                "tags": tags or [],
            }
        )


def log_solve(
    logger: RunLogger,
    *,
    solver,
    status,
    objective=None,
    solve_time=None,
    params_hash=None,
    code_hash=None,
    binding=None,
    extra=None,
):
    logger.write(
        {
            "kind": "solve",
            "solver": solver,
            "status": status,
            "objective": objective,
            "solve_time_s": solve_time,
            "params_hash": params_hash,
            "code_hash": code_hash,
            # optional: the set of binding constraints (used by E1's L3)
            "binding": binding,
            "extra": extra or {},
        }
    )


class _LoggedCompletions:
    def __init__(self, inner, logger, family, strategy):
        self._inner = inner
        self._logger = logger
        self._family = family
        self._strategy = strategy

    def create(self, **kwargs):
        t0 = time.time()
        resp = self._inner.create(**kwargs)
        latency = time.time() - t0
        try:
            text = resp.choices[0].message.content or ""
        except Exception:
            text = str(resp)
        usage = {}
        try:
            usage = {
                "prompt_tokens": resp.usage.prompt_tokens,
                "completion_tokens": resp.usage.completion_tokens,
            }
        except Exception:
            pass
        self._logger.log_llm(
            model=kwargs.get("model", "?"),
            family=self._family,
            strategy=self._strategy,
            request=kwargs,
            response_text=text,
            usage=usage,
            latency_s=round(latency, 3),
        )
        return resp


class _LoggedChat:
    def __init__(self, inner, logger, family, strategy):
        self.completions = _LoggedCompletions(inner.completions, logger, family, strategy)


class LoggedOpenAIClient:
    """Transparent proxy: intercepts chat.completions.create only, and
    forwards every other attribute untouched."""

    def __init__(self, client, logger, family, strategy):
        self._client = client
        self.chat = _LoggedChat(client.chat, logger, family, strategy)

    def __getattr__(self, name):
        return getattr(self._client, name)


def wrap_openai_client(client, logger: RunLogger, family: str, strategy: str):
    return LoggedOpenAIClient(client, logger, family, strategy)


# ---- self-test ----
if __name__ == "__main__":
    lg = RunLogger("runs/selftest.jsonl", run_id="selftest", operator="ci")
    lg.log_llm(
        model="dummy",
        family="test",
        strategy="none",
        request={
            "model": "dummy",
            "temperature": 0,
            "messages": [{"role": "user", "content": "hi"}],
        },
        response_text="hello",
        usage={"prompt_tokens": 1, "completion_tokens": 1},
        latency_s=0.01,
    )
    log_solve(
        lg,
        solver="highs",
        status="optimal",
        objective=960.0,
        solve_time=0.02,
        params_hash=content_hash({"p": 1}),
    )
    n = sum(1 for _ in open("runs/selftest.jsonl", encoding="utf-8"))
    print(f"selftest OK, {n} records written -> runs/selftest.jsonl")
