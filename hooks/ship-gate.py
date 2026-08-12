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
import os
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
            # Name the interpreter: on Windows `python` and `python3` can be
            # different installs, and a gate certified under one while the team
            # works under the other is a silent mismatch. QC caught exactly this
            # by checking both before re-running.
            interp = f"{Path(sys.executable).name} {sys.version_info.major}.{sys.version_info.minor}"
            write_gate(root, "QA-PASS", digest,
                       f"hook-verified: Ran {ran}, skipped {skipped} (via {interp})")
        else:
            empty = (ran == 0)
            why = ("The suite COLLECTED ZERO TESTS. Test files exist but the runner "
                   "matched none of them — for example pytest-style bare functions "
                   "under `unittest`, which only collects TestCase subclasses. Nothing "
                   "was executed, so nothing is certified. Make the suite discoverable "
                   "by the runner, or configure the runner it is written for."
                   if empty else
                   "The test suite does not pass.")
            if attempts(root, digest) >= MAX_BLOCKS:
                ok(f"ADVISORY: {why} This gate has already refused {MAX_BLOCKS} times. "
                   "Standing down — but nothing here is shippable.", "Stop")
            attempts(root, digest, bump=True)
            block("SHIP GATE — QA PASS DENIED\n" + why + "\n"
                  "This hook writes the QA gate itself and will not write it for a suite "
                  "that did not run and pass.")

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
    gate_py = Path(__file__).parent / "gate.py"
    # Only instruct the gates this muster actually requires. Printing a BIZ-ACCEPT
    # command to a SKIRMISH that has no Business team invites recording a gate no
    # one verified — the hook would be coaching the false PASS it exists to stop.
    hint = {"QC-TRUE": "<what was verified, with the commands>",
            "BIZ-ACCEPT": "<acceptance criteria met>"}
    # os.fspath keeps the platform's own separators; an f-string joining Path
    # fragments with "/" produced C:\Users\...\hooks/gate.py on Windows.
    lines = [f'  "{sys.executable}" "{os.fspath(gate_py)}" {g} "{hint[g]}"'
             for g in required_gates(root)]
    block(
        "SHIP GATE — REFUSED\n"
        + "\n".join("  " + m for m in missing)
        + f"\n\ndeliverables/ hashes to {digest}; every gate is bound to that hash, so any "
        "edit invalidates prior gates. Have the responsible team verify and record:\n"
        + "\n".join(lines)
        + "\nRecording a gate that was not verified is a false PASS — the gravest defect "
        "there is."
        + "\n\nAct on this refusal only. Do not restate the report you were about to end "
        "on — the operator has already read it, and repeating it is noise on top of a "
        "blocked turn."
    )


if __name__ == "__main__":
    main()
