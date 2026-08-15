# -*- coding: utf-8 -*-
"""AdmitOR release tooling -- scrub_logs.py

Purpose
    Produce publishable copies of run logs, cached responses and run
    manifests. Raw operational artifacts can carry request headers, relay
    base URLs, Authorization fields, key fragments and absolute local paths.
    This script strips all of that before anything reaches the release tree.

    It is committed so that the scrubbing process is auditable: a reader can
    check exactly what was removed and reproduce the transformation.

    Two transformations are applied.

    1. Sensitive keys. Any object key matching
           (?i)(api[_-]?key|authorization|token|secret|base_url|endpoint|proxy)
       is redacted. By default the key is kept with its value replaced by
       "[REDACTED]", which keeps the record shape intact and makes the
       redaction visible; --drop removes the key entirely instead. Matching
       is applied at every depth, including inside arrays, and to header
       dictionaries nested anywhere in the record.

    2. Absolute local paths. Windows paths (E:\\..., C:\\Users\\...) and POSIX
       home paths (/home/..., /Users/...) are rewritten to the relative
       placeholder "<PATH>/..." wherever they appear in any string value,
       including inside prompt and response text.

    In addition, any literal string supplied through --extra-secret (repeatable)
    or listed one-per-line in a --secrets-file is replaced with "[REDACTED]"
    anywhere it occurs. Use this for the operator's own endpoint hostnames
    and key values, which cannot be recognized structurally.

    Originals are never modified. Every output is written to a new location.

Inputs
    One or more input paths. A .jsonl input is scrubbed line by line; a .json
    input is scrubbed as a single document; a directory is walked and every
    .json and .jsonl file under it is scrubbed, preserving relative layout.

Outputs
    Scrubbed copies under --out-dir, plus a one-line summary per file and a
    final total on stdout. Exit code is non-zero if any input could not be
    read.

Example invocation (from the repository root)
    python release_tools/scrub_logs.py ../OptSkills-main/runs/host_llm.jsonl \\
        --out-dir artifacts/runlogs --secrets-file ../secrets_to_strip.txt
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

SENSITIVE_KEY = re.compile(r"(?i)(api[_-]?key|authorization|token|secret|base_url|endpoint|proxy)")

# Windows drive-letter paths and POSIX home paths. Kept deliberately greedy on
# the path body but stopped at quotes, whitespace and common JSON delimiters.
ABS_PATH = re.compile(
    r"(?:[A-Za-z]:[\\/]{1,2}[^\s\"'<>|]*" r"|/home/[^\s\"'<>|:]*" r"|/Users/[^\s\"'<>|:]*)"
)

REDACTED = "[REDACTED]"
PATH_PLACEHOLDER = "<PATH>"


def _can_hold_secret(value) -> bool:
    """Whether a value under a sensitive-looking key could actually carry a
    credential.

    The key pattern above is deliberately broad, and one of its alternatives,
    `token`, also matches the usage counters every OpenAI-compatible response
    carries: prompt_tokens, completion_tokens, total_tokens. Those are
    integers, and blanking them would destroy the token accounting the run
    ledger exists to provide while protecting nothing.

    A credential is always text. Numbers, booleans and nulls cannot hold one,
    so they are left intact; strings and any nested structure are redacted.
    This narrows the rule only where it is provably safe to do so.
    """
    return not isinstance(value, (int, float, bool, type(None)))


class Scrubber:
    def __init__(self, drop: bool = False, extra_secrets=()):
        self.drop = drop
        # Longest first, so that a longer secret containing a shorter one is
        # replaced as a whole rather than being partially masked.
        self.extra = sorted({s for s in extra_secrets if s.strip()}, key=len, reverse=True)
        self.redactions = 0
        self.paths_rewritten = 0
        self.secrets_masked = 0

    def scrub_text(self, s: str) -> str:
        def _path_sub(m):
            self.paths_rewritten += 1
            return PATH_PLACEHOLDER + "/..."

        out = ABS_PATH.sub(_path_sub, s)
        for secret in self.extra:
            if secret in out:
                self.secrets_masked += out.count(secret)
                out = out.replace(secret, REDACTED)
        return out

    def scrub(self, obj):
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if isinstance(k, str) and SENSITIVE_KEY.search(k) and _can_hold_secret(v):
                    self.redactions += 1
                    if not self.drop:
                        out[k] = REDACTED
                    continue
                out[k] = self.scrub(v)
            return out
        if isinstance(obj, list):
            return [self.scrub(v) for v in obj]
        if isinstance(obj, str):
            return self.scrub_text(obj)
        return obj


def iter_inputs(paths):
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                for name in sorted(files):
                    if name.endswith((".json", ".jsonl")):
                        full = os.path.join(root, name)
                        yield full, os.path.relpath(full, p)
        else:
            yield p, os.path.basename(p)


def scrub_file(src: str, dst: str, sc: Scrubber) -> tuple:
    os.makedirs(os.path.dirname(os.path.abspath(dst)), exist_ok=True)
    records = bad = 0
    if src.endswith(".jsonl"):
        with open(src, encoding="utf-8") as fin, open(
            dst, "w", encoding="utf-8", newline="\n"
        ) as fout:
            for line in fin:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    # A malformed line cannot be structurally scrubbed, so it
                    # is dropped rather than passed through unexamined.
                    bad += 1
                    continue
                fout.write(json.dumps(sc.scrub(rec), ensure_ascii=False) + "\n")
                records += 1
    else:
        with open(src, encoding="utf-8") as fin:
            doc = json.load(fin)
        with open(dst, "w", encoding="utf-8", newline="\n") as fout:
            json.dump(sc.scrub(doc), fout, ensure_ascii=False, indent=2)
        records = 1
    return records, bad


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Write scrubbed copies of run logs and manifests into a "
        "release tree. Originals are never modified."
    )
    ap.add_argument("inputs", nargs="+", help="files or directories to scrub")
    ap.add_argument(
        "--out-dir", required=True, help="destination directory for the scrubbed copies"
    )
    ap.add_argument(
        "--drop",
        action="store_true",
        help="remove sensitive keys entirely instead of replacing " "their values with [REDACTED]",
    )
    ap.add_argument(
        "--extra-secret",
        action="append",
        default=[],
        help="literal string to mask anywhere it appears; may be " "repeated",
    )
    ap.add_argument(
        "--secrets-file",
        default="",
        help="file of additional literal secrets, one per line; "
        "blank lines and lines starting with # are ignored",
    )
    a = ap.parse_args()

    extra = list(a.extra_secret)
    if a.secrets_file:
        with open(a.secrets_file, encoding="utf-8") as f:
            extra += [l.strip() for l in f if l.strip() and not l.startswith("#")]

    sc = Scrubber(drop=a.drop, extra_secrets=extra)
    total_records = total_bad = 0
    failures = 0
    for src, rel in iter_inputs(a.inputs):
        dst = os.path.join(a.out_dir, rel)
        try:
            n, bad = scrub_file(src, dst, sc)
        except Exception as exc:
            print(f"[scrub] FAILED {src}: {type(exc).__name__}: {exc}")
            failures += 1
            continue
        total_records += n
        total_bad += bad
        note = f", {bad} unparseable line(s) dropped" if bad else ""
        print(f"[scrub] {src} -> {dst}: {n} record(s){note}")

    print(
        f"[scrub] done: {total_records} record(s), "
        f"{sc.redactions} sensitive field(s) "
        f"{'dropped' if a.drop else 'redacted'}, "
        f"{sc.paths_rewritten} absolute path(s) rewritten, "
        f"{sc.secrets_masked} literal secret occurrence(s) masked, "
        f"{total_bad} unparseable line(s) dropped"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
