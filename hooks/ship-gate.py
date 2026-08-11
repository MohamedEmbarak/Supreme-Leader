#!/usr/bin/env python3
"""Stop — the ship gates, enforced.

Nothing ships ungated. As prose that is a promise; here it is a precondition for
ending the turn. Gates are bound to a content hash of deliverables/, so any edit
invalidates every gate that preceded it. QA-PASS is not claimable at all: this hook
writes it, and only after the suite actually passes.

Muster-aware: a FULL muster requires QC-TRUE + BIZ-ACCEPT; a SKIRMISH muster
requires QC-TRUE only (there is no Business team on the field to accept).

Inactive projects: one stat() and out. Loop safety: after MAX_BLOCKS refusals on
the same hash the hook downgrades to advisory — a hook that can trap the
conversation is worse than one that can be ignored.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    block, deliverables_hash, ok, org_active, org_field, project_dir, read_event,
    read_gate, run_suite, state_dir, write_gate,
)

MAX_BLOCKS = 3


def required_gates(root):
    muster = org_field(root, "MUSTER", "FULL").upper()
    return ["QC-TRUE"] if "SKIRMISH" in muster else ["QC-TRUE", "BIZ-ACCEPT"]


def attempts(root, digest, bump=False):
    p = state_dir(root) / "attempts.json"
    data = {}
    if p.is_file():
        try:
            data = json.loads(p.read_text())
        except Exception:
            data = {}
    n = data.get(digest, 0)
    if bump:
        p.write_text(json.dumps({digest: n + 1}))
    return n


def main():
    root = project_dir()
    if not org_active(root):
        ok()
    read_event()

    digest = deliverables_hash(root)
    if not digest:
        ok()  # nothing produced yet; nothing to gate

    suite = run_suite(root)
    if suite and suite[0] != "ERROR":
        ran, passed, skipped, _ = suite
        if passed:
            write_gate(root, "QA-PASS", digest, f"hook-verified: Ran {ran}, skipped {skipped}")
        else:
            if attempts(root, digest) >= MAX_BLOCKS:
                ok(f"ADVISORY: the suite does not pass and this gate has already refused "
                   f"{MAX_BLOCKS} times. Standing down — but nothing here is shippable.",
                   "Stop")
            attempts(root, digest, bump=True)
            block("SHIP GATE — QA PASS DENIED\n"
                  "The test suite does not pass. This hook writes the QA gate itself and "
                  "will not write it for a failing suite. Fix the failures, then stop.")

    missing = []
    for name in required_gates(root):
        g = read_gate(root, name)
        if g is None:
            missing.append(f"{name}: never recorded")
        elif g.get("deliverables") != digest:
            missing.append(f"{name}: STALE — recorded against {g.get('deliverables')}, "
                           f"deliverables are now {digest}")

    if not missing:
        ok()

    if attempts(root, digest) >= MAX_BLOCKS:
        ok("ADVISORY: ship gates unsatisfied (" + "; ".join(missing) +
           f") after {MAX_BLOCKS} refusals. Standing down; whatever ships now, ships "
           "ungated.", "Stop")

    attempts(root, digest, bump=True)
    hook_dir = Path(__file__).parent
    block(
        "SHIP GATE — REFUSED\n"
        + "\n".join("  " + m for m in missing)
        + f"\n\ndeliverables/ hashes to {digest}; every gate is bound to that hash, so any "
        "edit invalidates prior gates. Have the responsible team verify and record:\n"
        f"  python3 \"{hook_dir}/gate.py\" QC-TRUE    \"<what was verified, with commands>\"\n"
        f"  python3 \"{hook_dir}/gate.py\" BIZ-ACCEPT \"<criteria met>\"\n"
        "Recording a gate that was not verified is a false PASS — the gravest defect there is."
    )


if __name__ == "__main__":
    main()
