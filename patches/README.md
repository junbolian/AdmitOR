# Host patches

AdmitOR runs inside the OptSkills skill-learning host. Three behavioral
changes to that host were needed for the experiments in the paper. This
directory ships them as unified diffs against the pristine upstream files.

No OptSkills source is redistributed here. You need your own checkout of the
host, and these patches apply on top of it.

## Upstream

| | |
|---|---|
| Repository | https://github.com/fujiwaranoM0kou/OptSkills |
| Commit | `7d3194098e17f8f032359d8ad507bbe6bfc208fa` |
| Commit date | 2026-06-25 |
| Commit subject | Revise citation for MiniOpt and add OptSkills |
| Upstream licence | MIT (Copyright (c) 2026 Haochen Yang) |
| Paper | OptSkills, arXiv:2605.29829 |

The upstream licence is MIT and does permit redistributing modified copies.
We ship patches anyway, so that what is ours and what is theirs stays
unambiguous and so that the host stays on whatever revision its maintainers
publish.

## Applying

Clone the host at the pinned commit, then apply both patches from the host
root:

```
git clone https://github.com/fujiwaranoM0kou/OptSkills.git
cd OptSkills
git checkout 7d3194098e17f8f032359d8ad507bbe6bfc208fa
git apply /path/to/AdmitOR/patches/llm_caller.patch
git apply /path/to/AdmitOR/patches/runner.patch
```

The patches are LF-normalized. On Windows, clone with
`git clone -c core.autocrlf=false ...`, or apply with
`git apply --ignore-whitespace`, or use `patch -p1 < <file>` which is
line-ending tolerant.

Verify both applied:

```
git diff --stat
```

You should see `llm/llm_caller.py` and `pipeline/runner.py` modified, and
nothing else.

## What each patch does

### `llm_caller.patch` -> `llm/llm_caller.py`

Adds three opt-in hooks around the host's chat-completions transport. Every
one of them is inert unless its environment variable is set, so with no
environment set the host behaves exactly as it does upstream.

1. **Run logging.** On every successful call, and on terminal failure, one
   record is appended to a JSONL ledger through `scripts/runlog.py`. Only
   content hashes, sizes, token usage and latency are recorded, never prompt
   or response bodies. This is what produces the per-call run log shipped in
   `artifacts/runlogs/`. If `runlog.py` cannot be imported or anything in the
   hook raises, the exception is swallowed and the host call proceeds
   normally: the hook can never change the host's result.
2. **Response cache.** With `ADMITOR_CACHE=<dir>`, successful responses are
   cached keyed by the sha256 of the exact request body. At temperature 0 an
   identical request is the identical computation, so a long monolithic
   rebuild that dies part-way replays its completed calls for free on the
   next attempt. This is a retry-economics measure only; it never changes
   what a fresh call returns. Unset, there are no cache reads or writes.
3. **Retry override.** With `ADMITOR_RETRIES=<n>`, the attempt count is
   raised and the backoff becomes exponential capped at 60 seconds, so a
   transient relay drop is absorbed inside the call instead of escalating to
   a phase-fatal error upstream. Unset, the stock retry policy is
   byte-identical to upstream.

Environment variables read by this patch:

| Variable | Default | Meaning |
|---|---|---|
| `ADMITOR_SCRIPTS` | `./scripts` | directory containing `runlog.py` |
| `ADMITOR_RUNLOG` | `runs/host_llm.jsonl` | ledger output path |
| `ADMITOR_RUN_ID` | `host` | run id tag on every record |
| `ADMITOR_FAMILY` | `deepseek` | family tag on every record |
| `ADMITOR_OPERATOR` | `unknown` | operator tag on every record |
| `ADMITOR_CACHE` | unset | cache directory; unset disables the cache |
| `ADMITOR_RETRIES` | unset | attempt count; unset keeps stock retries |

### `runner.patch` -> `pipeline/runner.py`

Makes a single sample's failure sample-fatal instead of phase-fatal, in both
worker loops. Upstream collects futures in a list and calls `future.result()`
unguarded, so one sample's exception propagates and kills the entire segment,
discarding the work of every sibling sample in flight.

Resume itself is upstream machinery and is not modified. What this patch
changes is that a failing sample no longer takes the phase down before resume
can make progress; on the next pass resume simply picks the skipped samples
up again.

1. **Cluster loop.** A failing sample is logged and skipped without being
   committed, so resume retries it on the next pass.
2. **Eval loop.** Two failure classes are separated. A deterministic failure,
   identified by `invalid skill_id` (a temperature-0 skill-selector
   hallucination that no retry can ever pass), is committed as a failed row:
   prediction `None`, scored wrong, exactly the treatment a solver failure
   gets. Without this the segment crash-loops forever on that one sample.
   Any other failure is treated as transient and skipped without commit, for
   resume to retry.

Rows committed by the deterministic branch carry `"e1_eval_failure": true`,
so they remain identifiable in the trajectories and are counted as wrong by
the scorer rather than quietly dropped. The 87 unparseable rows noted in the
README's GT/OptiBench footnote are visible through exactly this mechanism.

## Scope

These two files are the only host files AdmitOR modifies. Everything else in
this repository runs outside the host, reading its outputs.
