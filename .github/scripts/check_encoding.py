#!/usr/bin/env python3
"""Every tracked text file must decode as UTF-8.

Three files reached main encoded UTF-16LE (#1345): `backend/requirements.txt`,
which made `pip install -r requirements.txt` fail outright and took Backend CI
with it, and the two recruiter modules, which TypeScript could not parse.

Nothing caught them, and the reason is worth stating because it rules out the
obvious implementation. Every other guard in `.github/workflows` is built on
`git grep`, and `git grep` skips binary files -- a file full of NUL bytes is
binary as far as Git is concerned. `git grep -l recruiterApi` does not find the
module that *defines* `recruiterApi`. So this reads the bytes itself.

`git ls-files` gives the tracked set. Files Git has recorded as binary via
.gitattributes, and paths that are genuinely binary by extension, are skipped;
everything else has to decode.
"""

from __future__ import annotations

import subprocess
import sys

# Extensions whose contents are not text and are not expected to decode.
BINARY_SUFFIXES = {
    ".ico", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".avif", ".bmp",
    ".pdf", ".zip", ".gz", ".tgz", ".bz2", ".xz", ".7z", ".jar",
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    ".mp3", ".mp4", ".webm", ".mov", ".wav", ".ogg",
    ".so", ".dylib", ".dll", ".exe", ".pyc", ".class", ".wasm",
    ".db", ".sqlite", ".sqlite3",
}


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files", "-z"], capture_output=True, check=True
    ).stdout
    return [p for p in out.decode("utf-8", "surrogateescape").split("\0") if p]


def is_binary_path(path: str) -> bool:
    dot = path.rfind(".")
    return dot != -1 and path[dot:].lower() in BINARY_SUFFIXES


def describe(data: bytes) -> str:
    """Name the encoding when it is one of the ones that actually turns up."""
    if data.startswith(b"\xff\xfe"):
        return "UTF-16LE (with BOM)"
    if data.startswith(b"\xfe\xff"):
        return "UTF-16BE (with BOM)"
    # A NUL in every other byte position is UTF-16 without a BOM, which is what
    # a PowerShell `>` or `>>` redirect writes.
    head = data[:512]
    if head.count(b"\x00") > len(head) // 4:
        return "UTF-16 (no BOM)"
    return "not valid UTF-8"


def main() -> int:
    bad: list[tuple[str, str]] = []

    for path in tracked_files():
        if is_binary_path(path):
            continue
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError:
            # Submodules and broken symlinks are not ours to check.
            continue
        if not data:
            continue
        try:
            data.decode("utf-8")
        except UnicodeDecodeError:
            bad.append((path, describe(data)))

    if bad:
        print("::error::Tracked text files are not UTF-8:")
        for path, why in bad:
            print(f"    {path}  --  {why}")
        print()
        print("  A UTF-16 file is binary to Git, so git grep skips it and every")
        print("  grep-based check in .github/workflows is blind to it. pip and")
        print("  tsc are not: both fail on the bytes.")
        print()
        print("  On Windows, `cmd > file` and PowerShell `>`/`>>` write UTF-16.")
        print("  Use `Set-Content -Encoding utf8` or write the file from an")
        print("  editor set to UTF-8.")
        return 1

    print(f"{len(tracked_files())} tracked files checked; all text files are UTF-8.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
