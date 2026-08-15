# -*- coding: utf-8 -*-
"""AdmitOR release tooling -- make_manifest.py

Purpose
    Build and verify artifacts/MANIFEST.md, the single table that lists every
    released artifact with its size, its sha256, and the paper table or
    figure it backs.

    Two modes:
      --verify (default)  recompute the sha256 and size of every path listed
                          in the manifest and report any mismatch, any
                          missing file, and any artifact present on disk but
                          absent from the manifest. Exit code is non-zero if
                          anything fails, so it can be used as a release gate.
      --write             regenerate the manifest's table rows in place from
                          what is on disk, preserving the prose sections and
                          the existing "backs" annotations.

    Release assets, meaning oversized artifacts that are attached to the
    GitHub Release rather than committed, are listed with an asset filename
    instead of a repository path. Those rows are verified against
    release_assets/<filename> when that directory exists locally, and are
    reported as "not present locally" otherwise rather than counted as
    failures.

Inputs
    --manifest  path to the manifest (default artifacts/MANIFEST.md)
    --root      repository root that manifest paths are relative to
                (default the parent directory of release_tools)

Outputs
    A verification report on stdout. With --write, the manifest file is
    rewritten in place.

Example invocation (from the repository root)
    python release_tools/make_manifest.py
    python release_tools/make_manifest.py --write
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sys

ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|([^|]*)\|\s*`([0-9a-f]{64})`\s*\|(.*)\|\s*$")
ASSET_MARK = "(release asset)"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def walk_sorted(root: str):
    """Every file under root, as (relative posix path, absolute path), in a
    stable order that does not depend on the filesystem."""
    items = []
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            items.append((rel, full))
    items.sort()
    return items


def digest_dir(root: str) -> tuple:
    """Aggregate digest of a whole artifact collection.

    A collection is summarized by one hash so the manifest stays readable
    when a row stands for several hundred files. The digest is the sha256 of
    the lines "<relative path>\\t<file sha256>\\n" over every file, sorted by
    relative path, so it is reproducible on any platform and changes if any
    file is added, removed, renamed or edited.

    Returns (digest, total bytes, file count).
    """
    h = hashlib.sha256()
    total = count = 0
    for rel, full in walk_sorted(root):
        h.update(f"{rel}\t{sha256_file(full)}\n".encode("utf-8"))
        total += os.path.getsize(full)
        count += 1
    return h.hexdigest(), total, count


def size_str(nbytes: int) -> str:
    if nbytes < 1024:
        return f"{nbytes} B"
    if nbytes < 1024 * 1024:
        return f"{nbytes / 1024:.1f} KB"
    return f"{nbytes / (1024 * 1024):.1f} MB"


def parse_rows(text: str):
    """Yield (lineno, path, size_cell, sha, backs_cell) for every table row."""
    for i, line in enumerate(text.splitlines()):
        m = ROW.match(line.strip())
        if m:
            yield i, m.group(1).strip(), m.group(2).strip(), m.group(3), m.group(4).strip()


def resolve(root: str, path: str, backs: str) -> tuple:
    """Return (absolute path, is_release_asset)."""
    if ASSET_MARK in backs:
        return os.path.join(root, "release_assets", path), True
    return os.path.join(root, path), False


def verify(root: str, manifest: str) -> int:
    if not os.path.isfile(manifest):
        print(f"[manifest] MISSING: {manifest}")
        return 1
    text = open(manifest, encoding="utf-8").read()
    rows = list(parse_rows(text))
    if not rows:
        print(f"[manifest] no artifact rows parsed from {manifest}")
        return 1

    ok = missing = mismatched = skipped = 0
    listed = set()
    for _i, path, size_cell, sha, backs in rows:
        full, is_asset = resolve(root, path, backs)
        is_dir_row = path.endswith("/")

        if is_dir_row:
            if not os.path.isdir(full):
                missing += 1
                print(f"[manifest] MISS  {path}: directory not found")
                continue
            for _rel, member in walk_sorted(full):
                listed.add(os.path.normpath(member))
            got, nbytes, _n = digest_dir(full)
            got_size = size_str(nbytes)
        else:
            listed.add(os.path.normpath(full))
            if not os.path.isfile(full):
                if is_asset:
                    skipped += 1
                    print(
                        f"[manifest] SKIP  {path}: release asset not present "
                        f"locally (built at release time)"
                    )
                else:
                    missing += 1
                    print(f"[manifest] MISS  {path}: file not found")
                continue
            got = sha256_file(full)
            got_size = size_str(os.path.getsize(full))

        if got != sha:
            mismatched += 1
            print(f"[manifest] BAD   {path}")
            print(f"                  recorded {sha}")
            print(f"                  actual   {got}")
            continue
        if size_cell and got_size != size_cell:
            print(f"[manifest] note  {path}: size cell says {size_cell}, " f"file is {got_size}")
        ok += 1

    # Anything under artifacts/ that no row mentions is an unlisted artifact.
    unlisted = []
    art = os.path.join(root, "artifacts")
    for dirpath, _dirs, files in os.walk(art):
        for name in files:
            full = os.path.normpath(os.path.join(dirpath, name))
            if name == "MANIFEST.md":
                continue
            if full not in listed:
                unlisted.append(os.path.relpath(full, root))

    print(
        f"\n[manifest] {ok} verified, {mismatched} mismatched, "
        f"{missing} missing, {skipped} release asset(s) not local, "
        f"{len(unlisted)} unlisted file(s) under artifacts/"
    )
    if unlisted:
        for u in unlisted[:20]:
            print(f"[manifest] UNLISTED {u}")
        if len(unlisted) > 20:
            print(f"[manifest] ... and {len(unlisted) - 20} more")
    return 1 if (mismatched or missing or unlisted) else 0


def write(root: str, manifest: str) -> int:
    """Recompute the size and sha256 cells of every existing row in place."""
    text = open(manifest, encoding="utf-8").read()
    lines = text.splitlines()
    changed = 0
    for i, path, _size_cell, sha, backs in parse_rows(text):
        full, is_asset = resolve(root, path, backs)
        if path.endswith("/"):
            if not os.path.isdir(full):
                print(f"[manifest] cannot refresh missing directory: {path}")
                continue
            new_sha, nbytes, _n = digest_dir(full)
            new_size = size_str(nbytes)
        else:
            if not os.path.isfile(full):
                if not is_asset:
                    print(f"[manifest] cannot refresh missing file: {path}")
                continue
            new_sha = sha256_file(full)
            new_size = size_str(os.path.getsize(full))
        line = f"| `{path}` | {new_size} | `{new_sha}` | {backs} |"
        if lines[i] != line:
            lines[i] = line
            changed += 1
    open(manifest, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    print(f"[manifest] rewrote {changed} row(s) in {manifest}")
    return 0


def main() -> int:
    default_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="Build or verify artifacts/MANIFEST.md.")
    ap.add_argument(
        "--manifest",
        default=None,
        help="path to MANIFEST.md (default <root>/artifacts/MANIFEST.md)",
    )
    ap.add_argument(
        "--root", default=default_root, help="repository root that manifest paths are relative to"
    )
    ap.add_argument(
        "--write",
        action="store_true",
        help="refresh size and sha256 cells in place instead of " "verifying",
    )
    a = ap.parse_args()
    manifest = a.manifest or os.path.join(a.root, "artifacts", "MANIFEST.md")
    return write(a.root, manifest) if a.write else verify(a.root, manifest)


if __name__ == "__main__":
    sys.exit(main())
