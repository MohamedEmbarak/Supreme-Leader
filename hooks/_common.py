"""Shared helpers for the Supreme Leader enforcement hooks.

Design constraints, in order:

1. Honesty — a hook may only block on something it actually verified this run.
2. Weight — when no organization is active in the project, every hook must no-op
   in milliseconds. The check is one stat() on ORGANIZATION.md.
3. Containment — all run-state lives in .claude/sl/ inside the user's project,
   with a self-written .gitignore so it can never pollute their history.
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def project_dir():
    return Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path.cwd())


def org_file(root):
    return root / "ORGANIZATION.md"


def org_active(root):
    """The single activation switch: an organization exists in this project."""
    return org_file(root).is_file()


def org_field(root, key, default=""):
    """Read a `**KEY:** value` line from ORGANIZATION.md (e.g. MUSTER, REGISTER)."""
    try:
        text = org_file(root).read_text(encoding="utf-8", errors="replace")[:4000]
    except Exception:
        return default
    m = re.search(rf"\*\*{key}:\*\*\s*([^\n]+)", text)
    return m.group(1).strip() if m else default


def state_dir(root):
    d = root / ".claude" / "sl"
    d.mkdir(parents=True, exist_ok=True)
    gi = d / ".gitignore"
    if not gi.exists():
        gi.write_text("*\n")  # run-state is per-session, never framework
    return d


def read_event():
    try:
        return json.loads(sys.stdin.read() or "{}")
    except Exception:
        return {}


def block(reason):
    print(reason, file=sys.stderr)
    sys.exit(2)


def ok(context=None, event=None):
    if context and event:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": event, "additionalContext": context}}))
    sys.exit(0)


# --- test suite -----------------------------------------------------------------

CLAIM_RAN = re.compile(r"\bRan\s+(\d+)\s+tests?\b")
CLAIM_OK = re.compile(r"^\s*OK\b(?:\s*\(skipped=(\d+)\))?\s*$", re.M)
CLAIM_FAILED = re.compile(r"^\s*FAILED\b", re.M)


def find_suite(root):
    """Dotted module names for every test file, rooted at the project dir.

    Not `unittest discover`: a directory without __init__.py is not importable as
    a start dir, and the resulting ImportError is indistinguishable from a failing
    suite — which would make this hook block *truthful* claims.
    """
    mods = []
    for d in ("deliverables", "tests", "test", "src", "."):
        base = root / d
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("test_*.py")):
            if "__pycache__" in f.parts or ".venv" in f.parts:
                continue
            rel = f.relative_to(root).with_suffix("")
            mods.append(".".join(rel.parts))
        if mods:
            break
    return mods or None


def run_suite(root):
    """Execute the suite. Returns (ran, ok_flag, skipped, output) or None."""
    mods = find_suite(root)
    if not mods:
        return None
    try:
        p = subprocess.run(["python3", "-m", "unittest", "-v", *mods],
                           cwd=str(root), capture_output=True, text=True, timeout=300)
    except Exception as exc:
        return ("ERROR", False, 0, str(exc))
    out = (p.stdout or "") + (p.stderr or "")
    m = CLAIM_RAN.search(out)
    ran = int(m.group(1)) if m else None
    okm = CLAIM_OK.search(out)
    skipped = int(okm.group(1)) if (okm and okm.group(1)) else 0
    return (ran, bool(okm), skipped, out)


# --- gates ----------------------------------------------------------------------

def deliverables_hash(root):
    d = root / "deliverables"
    if not d.is_dir():
        return None
    h = hashlib.sha256()
    empty = True
    for f in sorted(p for p in d.rglob("*") if p.is_file()):
        if "__pycache__" in f.parts:
            continue
        empty = False
        h.update(str(f.relative_to(d)).encode())
        h.update(f.read_bytes())
    return None if empty else h.hexdigest()[:16]


def read_gate(root, name):
    p = state_dir(root) / f"gate-{name}.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def write_gate(root, name, digest, note=""):
    (state_dir(root) / f"gate-{name}.json").write_text(json.dumps(
        {"gate": name, "deliverables": digest, "note": note}, indent=2) + "\n")
