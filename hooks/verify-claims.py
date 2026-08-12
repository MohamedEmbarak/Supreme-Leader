#!/usr/bin/env python3
"""Repo-wide claim audit. Run by CI, and runnable by hand.

    python3 .claude/hooks/verify-claims.py

Walks every tracked markdown file, finds stated test results, and checks each against
an actual run of the suite. Exits non-zero on the first claim that does not reproduce.

The local hooks protect a session. This protects the repository — including from
contributors who never ran the hooks, and from claims that were true when written
and quietly expired afterwards. Staleness and fabrication are indistinguishable to
a reader; both are caught here.
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    CLAIM_FAILED, CLAIM_OK, HISTORICAL, claimed_totals, project_dir, run_suite,
)

# Declared at file top (whole file) or at end of a line (that line only).

SKIP_DIRS = {".git", "node_modules", "__pycache__", ".claude", ".venv"}
# Files that discuss claim-checking rather than making claims.
SKIP_FILES = {"verify-claims.py", "truth-lint.py", "_common.py"}


def main():
    root = project_dir()

    suite = run_suite(root)
    if suite is None:
        print("no test suite found — nothing to verify claims against")
        return 0
    ran, passed, skipped, out = suite
    if ran == "ERROR":
        print(f"::error::suite could not be executed: {out[:400]}")
        return 1

    print(f"actual: Ran {ran} tests | {'OK' if passed else 'NOT OK'} | skipped={skipped}\n")

    failures = []
    exempted = 0
    for f in sorted(root.rglob("*.md")):
        if SKIP_DIRS & set(f.parts) or f.name in SKIP_FILES:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        rel = f.relative_to(root)
        lines = text.splitlines()

        # An audit log records what was measured at a point in time. Superseded
        # figures in such a file are the record working, not a false claim — so a
        # file may declare itself historical. The marker is deliberately explicit
        # and greppable: exemptions must be visible to the next auditor.
        if HISTORICAL.search(text[:2000]):
            exempted += 1
            continue

        seen = set()
        for label, claimed, line in claimed_totals(text):
            if ran is None or claimed == ran or (line, claimed) in seen:
                continue
            if HISTORICAL.search(lines[line - 1] if line <= len(lines) else ""):
                exempted += 1
                continue
            seen.add((line, claimed))
            failures.append(f"{rel}:{line}: claims {claimed} tests ({label}), actual is {ran}")

        if CLAIM_OK.search(text) and not passed:
            failures.append(f"{rel}: claims the suite passes; it does not")
        if CLAIM_FAILED.search(text) and passed:
            failures.append(f"{rel}: claims a failure; the suite passes")

    if exempted:
        print(f"{exempted} claim(s)/file(s) exempted as historical record.\n")

    if failures:
        print("CLAIMS THAT DO NOT REPRODUCE:\n")
        for x in failures:
            print(f"  ::error::{x}")
        print(f"\n{len(failures)} unverified claim(s). Every figure in this repository must "
              f"reproduce, or be marked UNVERIFIED.")
        return 1

    print("every stated test result reproduces.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
