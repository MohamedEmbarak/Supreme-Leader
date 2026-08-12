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
    CLAIM_FAILED, CLAIM_OK, JS_EXTENSIONS, STDLIB, block, claimed_totals, ok,
    ledger_attests, org_active, phrase, project_dir, read_event, run_suite,
    unresolved_js_imports,
)


def ledger_evidence(root, text, line_no):
    """Was the claiming line itself ever printed by a command? Timestamp or None.

    Matches the written line rather than a reconstructed per-framework needle. A
    figure like pytest's states components that sum to the total — `9 passed, 1
    skipped` is a total of 10 — so searching for "10 passed" would never hit, and
    the check would report every honest pytest figure as unobserved. People paste
    runner output verbatim, which makes the line the natural thing to look for.
    """
    try:
        line = text.splitlines()[line_no - 1].strip()
    except IndexError:
        return None
    if len(line) < 6:
        return None  # too short to be evidence of anything
    return ledger_attests(root, line)


def banner(root):
    """The only thing the register changes here: what the refusal is called."""
    return phrase(root, "", "DOCTRINE §III — ")


def claimed_results(text):
    return {
        "totals": claimed_totals(text),
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
        if m in STDLIB:
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
            block(f"{banner(root)}{path.name} does not parse: {exc}\n"
                  f"A deliverable that cannot be parsed cannot be verified. Fix the syntax.")
        if missing:
            block(
                f"{banner(root)}FABRICATED IMPORT BLOCKED in {path.name}\n"
                f"These imports do not resolve in this environment: {', '.join(missing)}\n"
                f"An import that does not exist is a fabricated dependency. Either install it "
                f"and prove it imports, or rewrite using the standard library."
            )

    # --- check 2b: invented npm packages --------------------------------------
    if path.suffix in JS_EXTENSIONS and "deliverables" in path.parts:
        missing = unresolved_js_imports(path, root)
        if missing:
            block(
                f"{banner(root)}FABRICATED PACKAGE BLOCKED in {path.name}\n"
                f"Not in package.json and not installed: {', '.join(missing)}\n"
                f"A package name an agent invented is the most durable fabrication there "
                f"is — it survives review, and the name may belong to someone else "
                f"tomorrow. Add it to package.json and install it, or import something "
                f"that exists."
            )

    # --- check 1: claimed test results ---------------------------------------
    claim = claimed_results(text)
    if not claim["totals"] and not claim["ok"] and not claim["failed"]:
        ok()  # no claim made, nothing to verify

    actual = run_suite(root)
    if actual is None or actual[0] == "ERROR":
        # No suite to re-run, or it would not execute. Fall back to the ledger:
        # a figure that appears in a recorded result was at least observed once,
        # and one that appears nowhere was written rather than measured. Advisory
        # either way — unverifiable is not the same as proven false, and blocking
        # on the difference would stop honest work in a project this hook cannot
        # execute.
        why = ("no suite was found to verify it against" if actual is None
               else f"the suite could not be executed ({actual[3][:120]})")
        attested, unattested = [], []
        for label, claimed, line in claim["totals"]:
            when = ledger_evidence(root, text, line)
            (attested if when else unattested).append((line, claimed, when))
        if unattested:
            ok(f"{path.name} states a test result and {why}. "
               + "; ".join(f"line {ln}: {n} does not appear in any command output this "
                           f"session" for ln, n, _ in unattested)
               + ". If it was not observed, mark it UNVERIFIED rather than stating it.",
               "PostToolUse")
        if attested:
            ok(f"{path.name} states a test result and {why}, but the figure appears in "
               f"the evidence ledger (first seen {attested[0][2]}). Treated as observed, "
               f"not as reproduced.", "PostToolUse")
        ok(f"{path.name} states a test result and {why}.", "PostToolUse")

    ran, passed, skipped, out = actual

    problems = []
    for label, claimed, line in claim["totals"]:
        if ran is not None and claimed != ran:
            problems.append(f"  line {line}: claims {claimed} tests ({label} format) "
                            f"— actual: {ran}")
    if claim["ok"] and not passed:
        problems.append("  claims the suite passes — actual: the suite does NOT pass")
    if claim["failed"] and passed:
        problems.append("  claims a failure — actual: the suite passes")

    if problems:
        tail = "\n".join(out.strip().splitlines()[-6:])
        block(
            f"{banner(root)}UNVERIFIED TEST CLAIM BLOCKED in {path.name}\n"
            + "\n".join(problems)
            + f"\n\nThe suite was just re-run by this hook. Its actual tail:\n{tail}\n\n"
            f"Write the figure that reproduces, or remove the claim. Presenting output "
            f"that was never printed is fabrication, not staleness."
        )

    ok()


if __name__ == "__main__":
    main()
