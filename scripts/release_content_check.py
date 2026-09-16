"""Content gates for files shipped in the public repository.

Purpose: before a release commit, check that (1) no shipped file under
`release/` carries the answer vault (the vault file itself, a JSON `answer`
key holding a vault value, or a CSV column that reproduces all 300 vault
answers), (2) no shipped text file contains an absolute Windows path, and
(3) no file under `release/reviewer_round/09_extractions/` stores a request
header with credentials.

Inputs (all in git):
    --root     repository root (default `.`)
    --vault    vault labels, relative to root
               (default `datasets/vault/optmath-train-300-labels.jsonl`)
    --release  directory checked for vault content, relative to root
               (default `release`)

Candidate objective values in the derived verdict files are allowed: they are
already public in `artifacts/e1/certify_runs`. Columns that match some vault
answers are listed for inspection but fail only at 300 matched rows.

Reproduce:
    python scripts/release_content_check.py --root .

Output: printed report; exit 0 when all gates pass, 1 otherwise.
Paper location: none (release hygiene).
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys

TEXT_EXT = {".md", ".txt", ".csv", ".json", ".jsonl", ".py", ".yml", ".yaml", ".toml",
            ".cfg", ".ini", ".patch", ".diff", ".sh", ".ps1", ".tex", ".bib", ".cff", ""}
# A drive letter, a separator, then a path segment. Escaped newlines and tabs
# inside JSON-encoded code (`j:\n`, `Q:\\n`) are not paths; neither is a
# documentation placeholder such as `C:\\Users\\...`.
ABS_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:(?:\\{1,2}|/)(?!(?:n|t|r)(?![A-Za-z]))"
                      r"[A-Za-z0-9_$][A-Za-z0-9_.$ -]*(?![A-Za-z0-9_.$ -])(?![\\/]{1,2}\.\.\.)")
# Inside JSON a single backslash starts an escape, so a path needs `\\` or `/`.
ABS_PATH_JSON = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:(?:\\\\|/)(?!(?:n|t|r)(?![A-Za-z]))"
                           r"[A-Za-z0-9_$][A-Za-z0-9_.$ -]*")
CRED_KEYS = re.compile(r"(?i)[\"']?(authorization|api[_-]?key|x-api-key)[\"']?\s*[:=]")


def num(v):
    try:
        return float(str(v).strip())
    except (TypeError, ValueError):
        return None


def load_vault(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        if line.strip():
            r = json.loads(line)
            out["sample_%d" % int(r["idx"])] = num(r["answer"])
    return out


def same(a, b):
    return a is not None and b is not None and abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def shipped_files(root):
    out = subprocess.run(["git", "-C", root, "ls-files", "-co", "--exclude-standard", "-z"],
                         capture_output=True, check=True).stdout
    return sorted(p for p in out.decode("utf-8").split("\0") if p)


def row_id(row):
    for k in ("sample_id", "item", "id"):
        v = (row.get(k) or "").strip()
        if v:
            return v if v.startswith("sample_") else ("sample_" + v if v.isdigit() else v)
    return None


def check_vault(root, rel, vault, fails, notes):
    path = os.path.join(root, rel)
    if os.path.basename(rel) == "optmath-train-300-labels.jsonl":
        fails.append("vault file shipped: " + rel)
        return
    ext = os.path.splitext(rel)[1].lower()
    if ext in (".json", ".jsonl"):
        text = open(path, encoding="utf-8", errors="replace").read()
        docs = []
        try:
            docs = [json.loads(text)]
        except ValueError:
            for line in text.splitlines():
                try:
                    docs.append(json.loads(line))
                except ValueError:
                    pass
        for d in docs:
            stack = [d]
            while stack:
                o = stack.pop()
                if isinstance(o, dict):
                    sid = o.get("sample_id")
                    if "answer" in o and sid in vault and same(num(o["answer"]), vault[sid]):
                        fails.append("vault answer under key 'answer': %s (%s)" % (rel, sid))
                    stack.extend(o.values())
                elif isinstance(o, list):
                    stack.extend(o)
    elif ext == ".csv":
        with open(path, encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if not rows:
            return
        for col in rows[0].keys():
            hit = sum(1 for r in rows if row_id(r) in vault and same(num(r.get(col)), vault[row_id(r)]))
            if hit >= 300:
                fails.append("CSV column lists the 300 vault answers: %s [%s]" % (rel, col))
            elif hit:
                notes.append("column matches vault on %d of %d rows: %s [%s]" % (hit, len(rows), rel, col))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", default=".")
    ap.add_argument("--vault", default="datasets/vault/optmath-train-300-labels.jsonl")
    ap.add_argument("--release", default="release")
    a = ap.parse_args()
    vault = load_vault(os.path.join(a.root, a.vault))
    files = shipped_files(a.root)
    fails, notes, n_text, n_rel = [], [], 0, 0
    rel_prefix = a.release.strip("/\\").replace("\\", "/") + "/"
    for rel in files:
        path = os.path.join(a.root, rel)
        if not os.path.isfile(path):
            continue
        if rel.startswith(rel_prefix):
            n_rel += 1
            check_vault(a.root, rel, vault, fails, notes)
        if os.path.splitext(rel)[1].lower() not in TEXT_EXT:
            continue
        n_text += 1
        text = open(path, encoding="utf-8", errors="replace").read()
        rx = ABS_PATH_JSON if os.path.splitext(rel)[1].lower() in (".json", ".jsonl") else ABS_PATH
        for m in rx.finditer(text):
            fails.append("absolute path: %s:%d  %r" % (rel, text[:m.start()].count("\n") + 1,
                                                       m.group(0)[:40]))
        if "/09_extractions/" in "/" + rel:
            for m in CRED_KEYS.finditer(text):
                fails.append("credential header key: %s:%d" % (rel, text[:m.start()].count("\n") + 1))
    print("files under %s checked for vault content: %d" % (rel_prefix, n_rel))
    print("shipped text files checked for absolute paths: %d" % n_text)
    for n in notes:
        print("  note: " + n)
    if fails:
        print("CONTENT CHECK: %d failure(s)" % len(fails))
        print("\n".join("  " + f for f in fails))
        return 1
    print("CONTENT CHECK: pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
