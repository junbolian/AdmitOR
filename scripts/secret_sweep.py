"""Secret sweep over the files a git checkout would commit.

Purpose: fail a commit when a credential, a private hostname, or an identity
string appears in any tracked or untracked-but-not-ignored file.

Inputs:
    tree           a directory; when it is a git work tree, only the files from
                   `git ls-files -co --exclude-standard` are scanned, otherwise
                   every file under it (private, not distributed: the terms file)
    terms_file     one term per line; a plain line is matched literally
                   (case-sensitive), a line starting with `re:` is a regular
                   expression, `#` lines are comments. Keep this file outside
                   the repository.

Generic credential shapes (sk- keys, Bearer tokens, GitHub tokens, AWS key
ids, PEM private keys, api_key assignments) are always checked. No hostname
or identity string is embedded here; those belong in the terms file.

Reproduce:
    python secret_sweep.py <repo> <terms_file>

Output: prints the scanned file count and each hit as path:line [label]; the
matched text of a terms-file hit is never printed. Exit 0 on 0 hits, 1 otherwise.
"""
import argparse
import os
import re
import subprocess
import sys

GENERIC = [
    # not after a letter or digit, so words such as "risk-weighted" do not match
    ("sk- prefix", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_\-]{8,}")),
    ("api_key literal", re.compile(r"(?i)api[_-]?key\s*[=:]\s*['\"]?[A-Za-z0-9_\-]{8,}")),
    ("Bearer token", re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.]{16,}")),
    ("Authorization header", re.compile(r"(?i)authorization\s*[=:]\s*['\"]?[A-Za-z]+\s+\S{8,}")),
    ("GitHub token", re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}")),
    ("AWS key id", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("PEM private key", re.compile(r"-----BEGIN[A-Z ]*PRIVATE KEY-----")),
]
PLACEHOLDER = re.compile(r"your-key|your-endpoint|XXXX\.XXXXX|0000-0000|\.\.\.")


def load_terms(path):
    pats = []
    for i, raw in enumerate(open(path, encoding="utf-8")):
        s = raw.rstrip("\r\n")
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        if s.startswith("re:"):
            pats.append(("term #%d" % (i + 1), re.compile(s[3:])))
        else:
            pats.append(("term #%d" % (i + 1), re.compile(re.escape(s))))
    return pats


def list_files(tree):
    try:
        out = subprocess.run(["git", "-C", tree, "ls-files", "-co", "--exclude-standard", "-z"],
                             capture_output=True, check=True).stdout
        return [os.path.join(tree, p) for p in out.decode("utf-8").split("\0") if p]
    except (subprocess.CalledProcessError, FileNotFoundError):
        acc = []
        for dp, dirs, files in os.walk(tree):
            dirs[:] = [d for d in dirs if d != ".git"]
            acc.extend(os.path.join(dp, n) for n in files)
        return acc


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("tree")
    ap.add_argument("terms_file")
    a = ap.parse_args()
    terms = load_terms(a.terms_file)
    hits, scanned = [], 0
    for p in sorted(list_files(a.tree)):
        if not os.path.isfile(p):
            continue
        try:
            t = open(p, encoding="utf-8", errors="replace").read()
        except OSError:
            continue
        scanned += 1
        rel = os.path.relpath(p, a.tree).replace(os.sep, "/")
        for lbl, rx in GENERIC + terms:
            for m in rx.finditer(t):
                if lbl.startswith("term") is False and PLACEHOLDER.search(m.group(0)):
                    continue
                line = t[:m.start()].count("\n") + 1
                frag = "" if lbl.startswith("term") else "  " + m.group(0)[:60]
                hits.append("  %s:%d  [%s]%s" % (rel, line, lbl, frag))
    print("scanned %d files" % scanned)
    if not hits:
        print("SWEEP RESULT: 0 hits")
        return 0
    print("SWEEP RESULT: %d hit(s)" % len(hits))
    print("\n".join(hits))
    return 1


if __name__ == "__main__":
    sys.exit(main())
