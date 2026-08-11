#!/usr/bin/env python3
"""Record a directorate gate against the current state of deliverables/.

    python3 .claude/hooks/gate.py QC-TRUE "audited 4 claims; all reproduced by command"
    python3 .claude/hooks/gate.py BIZ-ACCEPT "19/19 acceptance criteria met"

The gate is stamped with a content hash of deliverables/. Any later edit invalidates
it, and the Stop hook will refuse to ship until it is re-recorded. QA-PASS cannot be
written here — the Stop hook writes that one itself, only after the suite passes.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import deliverables_hash, org_active, project_dir, write_gate  # noqa: E402

ALLOWED = {"QC-TRUE", "BIZ-ACCEPT"}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ALLOWED:
        print(f"usage: gate.py [{'|'.join(sorted(ALLOWED))}] \"<evidence>\"", file=sys.stderr)
        print("QA-PASS is written by the ship-gate hook after a real test run; it cannot "
              "be recorded by hand.", file=sys.stderr)
        return 1
    name = sys.argv[1]
    note = sys.argv[2] if len(sys.argv) > 2 else ""
    if not note.strip():
        print(f"{name} needs evidence. A gate without a stated basis is a false PASS.",
              file=sys.stderr)
        return 1

    root = project_dir()
    if not org_active(root):
        print("no ORGANIZATION.md in this project — there is no organization to gate for.",
              file=sys.stderr)
        return 1
    digest = deliverables_hash(root)
    if not digest:
        print("deliverables/ is empty — there is nothing to gate.", file=sys.stderr)
        return 1

    write_gate(root, name, digest, note)
    print(f"{name} recorded against deliverables {digest}")
    print(f"  basis: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
