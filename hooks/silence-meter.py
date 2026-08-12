#!/usr/bin/env python3
"""SubagentStop — the Law of Silence, measured.

Deliberately advisory. On this event exit 2 makes the sub-agent *keep working*,
which for a verbosity complaint would produce more text, not less — so this hook
never blocks. It measures, records to the evidence ledger, and hands the
orchestrator a number it did not have to trust anyone for.

The Doctrine's budgets: employee and senior cycle reports ≤6 lines, free-form
commentary ≤3 lines. A Lead Rollup carries three sections plus tables; 60 lines is
generous for that and still catches an essay.
"""

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    ok, org_active, phrase, project_dir, read_event, state_dir,
)

BUDGET = 60


LEADS = ("business-lead", "software-development-lead", "qa-lead", "qc-lead",
         "delivery-lead")


def main():
    root = project_dir()
    if not org_active(root):
        ok()
    event = read_event()
    msg = event.get("last_assistant_message") or ""
    agent = event.get("agent_type") or "unknown"
    if not any(l in agent for l in LEADS):
        ok()  # not one of ours; other subagents are none of our business
    lines = [l for l in msg.splitlines() if l.strip()]
    n = len(lines)

    try:
        p = state_dir(root) / "verbosity.log"
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "agent": agent, "lines": n, "budget": BUDGET,
                "over": n > BUDGET,
            }) + "\n")
    except Exception:
        pass

    if n > BUDGET:
        head = phrase(root, "REPORT LENGTH", "LAW OF SILENCE")
        tail = phrase(
            root,
            "Measured by hook, not estimated. Score it, and tighten the next directive "
            "to that team.",
            "Measured by hook, not estimated. A subordinate's verbosity is the Supreme "
            "Leader's shame: score it, and tighten the next directive to that directorate.",
        )
        ok(f"{head} — {agent} returned {n} non-empty lines against a {BUDGET}-line "
           f"rollup budget ({n - BUDGET} over). {tail}", "SubagentStop")
    ok()


if __name__ == "__main__":
    main()
