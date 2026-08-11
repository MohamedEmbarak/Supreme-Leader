#!/usr/bin/env python3
"""PostToolUse(Write|Edit) — the Law of Truth, enforced instead of requested.

Two checks, both mechanical:

1. Any file that states a test result must state one that reproduces. The hook
   re-runs the suite and diffs. This is finding QC-01 and QC-03 from cycle 3 as a
   script: a hand-edited "Ran 22 tests" becomes impossible to write, not merely
   possible to catch afterwards.

2. Any Python file written into deliverables/ must import only modules that
   actually resolve. An invented package is the canonical catastrophic fabrication.
   Checked by parsing the syntax tree, not by grepping the file head, so
   function-local imports are caught too.
"""

import ast
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    CLAIM_FAILED, CLAIM_OK, CLAIM_RAN, block, ok, org_active, project_dir, read_event,
    run_suite,
)


def claimed_results(text):
    ran = CLAIM_RAN.search(text)
    return {
        "ran": int(ran.group(1)) if ran else None,
        "ok": bool(CLAIM_OK.search(text)),
        "failed": bool(CLAIM_FAILED.search(text)),
    }


def check_imports(path, root):
    tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods.add(node.module.split(".")[0])
    missing = []
    for m in sorted(mods):
        if m in sys.stdlib_module_names:
            continue
        if list(root.rglob(f"{m}.py")) or list(root.rglob(f"{m}/__init__.py")):
            continue  # local module
        try:
            if importlib.util.find_spec(m) is None:
                missing.append(m)
        except (ImportError, ValueError, ModuleNotFoundError):
            missing.append(m)
    return missing


def main():
    root = project_dir()
    if not org_active(root):
        ok()  # no organization in this project; the hook stays out of the way
    event = read_event()
    fp = (event.get("tool_input") or {}).get("file_path")
    if not fp:
        ok()
    path = Path(fp)
    if not path.is_absolute():
        path = root / path
    if not path.is_file():
        ok()

    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        ok()

    # --- check 2: invented imports -------------------------------------------
    if path.suffix == ".py" and "deliverables" in path.parts:
        try:
            missing = check_imports(path, root)
        except SyntaxError as exc:
            block(f"DOCTRINE §III — {path.name} does not parse: {exc}\n"
                  f"A deliverable that cannot be parsed cannot be verified. Fix the syntax.")
        if missing:
            block(
                f"DOCTRINE §III — CATASTROPHIC FABRICATION BLOCKED in {path.name}\n"
                f"These imports do not resolve in this environment: {', '.join(missing)}\n"
                f"An import that does not exist is a fabricated dependency. Either install it "
                f"and prove it imports, or rewrite using the standard library."
            )

    # --- check 1: claimed test results ---------------------------------------
    claim = claimed_results(text)
    if claim["ran"] is None and not claim["ok"] and not claim["failed"]:
        ok()  # no claim made, nothing to verify

    actual = run_suite(root)
    if actual is None:
        ok(f"{path.name} states a test result but no suite was found to verify it against. "
           f"If the figure was not observed this session, mark it UNVERIFIED.", "PostToolUse")

    ran, passed, skipped, out = actual
    if ran == "ERROR":
        ok(f"{path.name} states a test result; the suite could not be executed to check it "
           f"({out[:200]}). Do not present the figure as observed until it runs.", "PostToolUse")

    problems = []
    if claim["ran"] is not None and ran is not None and claim["ran"] != ran:
        problems.append(f"  claimed 'Ran {claim['ran']} tests' — actual: Ran {ran} tests")
    if claim["ok"] and not passed:
        problems.append("  claimed the suite passes — actual: the suite does NOT pass")
    if claim["failed"] and passed:
        problems.append("  claimed a failure — actual: the suite passes")

    if problems:
        tail = "\n".join(out.strip().splitlines()[-6:])
        block(
            f"DOCTRINE §III — UNVERIFIED TEST CLAIM BLOCKED in {path.name}\n"
            + "\n".join(problems)
            + f"\n\nThe suite was just re-run by this hook. Its actual tail:\n{tail}\n\n"
            f"Write the figure that reproduces, or remove the claim. Presenting output that "
            f"was never printed is fabrication, not staleness."
        )

    ok()


if __name__ == "__main__":
    main()
