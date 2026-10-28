"""Pre-publication check: fails if the release tree contains credentials, personal data or private files.

    python tools/check_release.py                       built-in checks only
    python tools/check_release.py --deny-file PATH      also block every term listed in PATH (one per line;
                                                        keep that file OUTSIDE the repository)

Built-in checks: credential-looking assignments and keys, e-mail addresses, absolute home-directory paths,
and file names that usually hold secrets or run logs.  Exit code 1 lists every finding.
"""

from __future__ import annotations

import argparse
import fnmatch
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "reports"}
TEXT_SUFFIXES = {".py", ".md", ".json", ".txt", ".toml", ".cfg", ".ini", ".yml", ".yaml", ".csv", ".gitignore", ""}
CONTENT_PATTERNS = {
    "credential assignment": re.compile(r"(?i)\b(pass(word|wd)?|api[_-]?key|secret|token|auth)\s*[:=]\s*['\"][^'\"\s]{4,}"),
    "private key block": re.compile("-----BEGIN [A-Z ]*" + "PRIVATE KEY-----"),
    "cloud or API key": re.compile(r"\b(AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,}|gh[pousr]_[A-Za-z0-9]{30,})\b"),
    "e-mail address": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "home-directory path": re.compile(r"(?i)\b[A-Z]:[\\/]+(Users|Documents and Settings)[\\/]|/home/[a-z_][\w-]*/|/Users/[A-Za-z][\w-]*/"),
    "app-data path": re.compile("(?i)App" + "Data[\\\\/]"),
}
NAME_PATTERNS = ["*credential*", "*secret*", ".env", "*.env", "*.log", "*receipt*", "*approval*", "*.pem", "*.key",
                 "*cookie*", "*session*.json"]


def load_terms(path: Path | None) -> list[str]:
    if not path:
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")]


def scan(root: Path = ROOT, terms: list[str] = ()) -> list[str]:
    findings: list[str] = []
    term_patterns = [(t, re.compile(r"(?i)(?<![\w])" + re.escape(t) + r"(?![\w])")) for t in terms]
    for path in sorted(root.rglob("*")):
        if any(part in SKIP_DIRS for part in path.relative_to(root).parts) or not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        for pattern in NAME_PATTERNS:
            if fnmatch.fnmatch(path.name.lower(), pattern):
                findings.append(f"{rel}: file name matches '{pattern}'")
        if path.suffix.lower() not in TEXT_SUFFIXES or path.stat().st_size > 5_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for label, pattern in CONTENT_PATTERNS.items():
            for match in pattern.finditer(text):
                findings.append(f"{rel}:{text.count(chr(10), 0, match.start()) + 1}: {label}")
        for term, pattern in term_patterns:
            if pattern.search(text):
                findings.append(f"{rel}: contains a deny-listed term (#{terms.index(term) + 1})")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--deny-file", type=Path, help="private list of terms that must not appear (keep it outside the repo)")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args(argv)
    findings = scan(args.root, load_terms(args.deny_file))
    if findings:
        print("NOT READY - remove these before publishing:", *findings, sep="\n  ")
        return 1
    print(f"Release check passed: {args.root.name} ({'with' if args.deny_file else 'without'} a private deny-list).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
