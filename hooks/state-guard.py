#!/usr/bin/env python3
"""PreToolUse(Write|Edit) — the gates and the ledger are not agent-writable.

`gate.py` refuses to record QA-PASS, and the README said the gate "cannot be
claimed by an agent at all". That was true of the CLI and false of the filesystem:
writing `.claude/sl/gate-QA-PASS.json` directly produced a file reading
`hook-verified: Ran 412, skipped 0` that no run ever justified. The same hole let
`evidence.log` be authored by hand — and 2.2 made truth-lint *consult* the ledger
when it cannot re-run a suite, which turned a passive log into something worth
forging. Found by attacking the release rather than by using it.

The directory is gitignored, so a forged gate never appears in a diff. That is what
makes this worth a hook rather than a note: nothing downstream would show it.

Residual, stated plainly rather than papered over: this closes the Write and Edit
path. A shell redirect into `.claude/sl/` still lands, because a PreToolUse(Bash)
hook cannot reliably tell which files an arbitrary command will touch. The ledger
records the attempt, which is the honest half of the answer.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    JS_EXTENSIONS, block, ok, org_active, phrase, project_dir, read_event,
    unresolved_js_imports, unresolved_py_imports,
)

PROTECTED = ("gate-", "evidence.log", "verbosity.log", "attempts.json")


def check_content(root, path, content):
    """Refuse a fabricated dependency before the file exists.

    `truth-lint` runs PostToolUse, so it can only object *after* the bytes are on
    disk. The README said an unresolvable import "cannot be committed to a
    deliverable", and a user showed the opposite: the blocked file sitting in the
    Source Control pane, staged and ready. The model was told no; git was not.

    Checking the proposed content here makes the claim true for Write, which is
    where new files — and therefore invented package names — come from. Edit
    supplies only a fragment, so it stays with the post-write check; that split is
    stated in the README rather than glossed.
    """
    if "deliverables" not in path.parts:
        return
    banner = phrase(root, "", "DOCTRINE §III — ")
    if path.suffix == ".py":
        try:
            missing = unresolved_py_imports(content, root)
        except SyntaxError:
            return  # let the post-write check report the syntax error properly
        if missing:
            block(f"{banner}FABRICATED IMPORT REFUSED before writing {path.name}\n"
                  f"These imports do not resolve here: {', '.join(missing)}\n"
                  f"Nothing was written. Install the dependency and prove it imports, "
                  f"or use the standard library.")
    elif path.suffix in JS_EXTENSIONS:
        missing = unresolved_js_imports(path, root, source=content)
        if missing:
            block(f"{banner}FABRICATED PACKAGE REFUSED before writing {path.name}\n"
                  f"Not in package.json and not installed: {', '.join(missing)}\n"
                  f"Nothing was written. A package name an agent invented survives "
                  f"review and may belong to someone else tomorrow — this one does not "
                  f"reach disk.")


def main():
    root = project_dir()
    if not org_active(root):
        ok()
    event = read_event()
    fp = (event.get("tool_input") or {}).get("file_path")
    if not fp:
        ok()

    path = Path(fp)
    if not path.is_absolute():
        path = root / path
    try:
        rel = path.resolve().relative_to((root / ".claude" / "sl").resolve())
    except (ValueError, OSError):
        content = (event.get("tool_input") or {}).get("content")
        if isinstance(content, str):
            check_content(root, path, content)
        ok()  # not under the state directory; nothing else here is our business

    name = rel.name
    if not any(name.startswith(p) or name == p for p in PROTECTED):
        ok()

    banner = phrase(root, "", "DOCTRINE §III — ")
    block(
        f"{banner}RUN-STATE IS NOT WRITABLE BY HAND — refused write to .claude/sl/{rel}\n"
        "These files are the record that the enforcement layer produced, not material "
        "for an agent to author. QA-PASS is written by the ship-gate hook after a suite "
        "it ran itself passed; the ledger is written by the evidence hook from what "
        "commands actually returned.\n"
        "To record a gate you are entitled to, use the CLI:\n"
        f'  "{sys.executable}" "{Path(__file__).parent / "gate.py"}" QC-TRUE "<evidence>"\n'
        "Writing the file directly would be a false PASS with the paperwork attached."
    )


if __name__ == "__main__":
    main()
