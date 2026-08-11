"""Shared helpers for the Supreme Leader enforcement hooks.

Design constraints, in order:

1. Honesty — a hook may only block on something it actually verified this run.
2. Weight — when no organization is active in the project, every hook must no-op
   in milliseconds. The check is one stat() on ORGANIZATION.md.
3. Containment — all run-state lives in .claude/sl/ inside the user's project,
   with a self-written .gitignore so it can never pollute their history.
"""

import hashlib
import importlib.util
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

# Written test-count claims, per framework. Deliberately anchored to the shapes
# real runners emit, so ordinary prose ("all 12 passed review") is not mistaken
# for a fabricated figure. Each yields the claimed TOTAL.
CLAIM_PATTERNS = [
    ("unittest", re.compile(r"\bRan\s+(\d+)\s+tests?\b")),
    ("node-tap", re.compile(r"^#\s*tests\s+(\d+)\s*$", re.M)),
    ("jest",     re.compile(r"^\s*Tests:\s+.*?(\d+) total", re.M)),
]
# pytest-style summaries state components rather than a total, so they are
# summed rather than read directly.
CLAIM_PYTEST = re.compile(
    r"^\s*(?=.*\b\d+ (?:passed|failed)\b)"
    r"(?:\d+ (?:passed|failed|skipped|error[s]?|xfailed|deselected)(?:, )?)+"
    r"(?: in [\d.]+s)?\s*$", re.M)
CLAIM_PYTEST_PART = re.compile(r"(\d+) (passed|failed|skipped|errors?)")


def claimed_totals(text):
    """Every test-count total asserted in text, as (label, total, line_no)."""
    out = []
    for label, rx in CLAIM_PATTERNS:
        for m in rx.finditer(text):
            out.append((label, int(m.group(1)), text[:m.start()].count("\n") + 1))
    for m in CLAIM_PYTEST.finditer(text):
        parts = CLAIM_PYTEST_PART.findall(m.group(0))
        total = sum(int(n) for n, kind in parts if kind != "deselected")
        if total:
            out.append(("pytest", total, text[:m.start()].count("\n") + 1))
    return out


def _python_test_modules(root):
    """Dotted module names for every Python test file, rooted at the project dir.

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
            if {"__pycache__", ".venv", "node_modules"} & set(f.parts):
                continue
            mods.append(".".join(f.relative_to(root).with_suffix("").parts))
        if mods:
            break
    return mods


def _pytest_usable(root):
    """pytest must be importable by *this* interpreter, and the project must ask
    for it. A pytest binary on PATH in its own isolated environment cannot run a
    suite that imports project modules — treating it as available is how a hook
    reports a spurious failure."""
    try:
        if importlib.util.find_spec("pytest") is None:
            return False
    except Exception:
        return False
    if (root / "pytest.ini").is_file() or (root / "conftest.py").is_file():
        return True
    pp = root / "pyproject.toml"
    return pp.is_file() and "[tool.pytest" in pp.read_text(errors="replace")


def detect_suite(root):
    """Return (kind, argv) for the project's test suite, or None.

    Manifests win over file-sniffing: a repo with a package.json test script is a
    Node project even if it also vendors a Python helper with a test file.
    """
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            scripts = (json.loads(pkg.read_text(errors="replace")).get("scripts") or {})
        except Exception:
            scripts = {}
        if scripts.get("test"):
            return ("node", ["npm", "test", "--silent"])

    if (root / "go.mod").is_file():
        return ("go", ["go", "test", "-v", "./..."])

    mods = _python_test_modules(root)
    if mods:
        if _pytest_usable(root):
            return ("pytest", [sys.executable, "-m", "pytest", "-q"])
        return ("unittest", [sys.executable, "-m", "unittest", "-v", *mods])
    return None


# Suite-summary parsers. Each returns (total, passed, skipped) or None.
def _parse_unittest(out):
    m = CLAIM_RAN.search(out)
    if not m:
        return None
    okm = CLAIM_OK.search(out)
    return (int(m.group(1)), bool(okm), int(okm.group(1)) if okm and okm.group(1) else 0)


def _parse_pytest(out):
    passed = re.search(r"(\d+) passed", out)
    failed = re.search(r"(\d+) (?:failed|error)", out)
    skipped = re.search(r"(\d+) skipped", out)
    if not (passed or failed):
        return None
    npass = int(passed.group(1)) if passed else 0
    nskip = int(skipped.group(1)) if skipped else 0
    nfail = int(failed.group(1)) if failed else 0
    return (npass + nfail + nskip, nfail == 0, nskip)


def _parse_node(out):
    """node --test emits TAP; jest and vitest emit their own summary lines.

    Formats verified against the real runners rather than recalled: node's TAP
    summary is `# tests N / # pass N / # fail N / # skipped N`, which shares no
    shape with jest's `Tests: 1 failed, 9 passed, 10 total`.
    """
    tap_total = re.search(r"^# tests (\d+)", out, re.M)
    if tap_total:
        fail = re.search(r"^# fail (\d+)", out, re.M)
        skip = re.search(r"^# skipped (\d+)", out, re.M)
        return (int(tap_total.group(1)),
                int(fail.group(1)) == 0 if fail else True,
                int(skip.group(1)) if skip else 0)

    m = re.search(r"^\s*Tests:?\s+(.*)$", out, re.M)
    if not m:
        return None
    line = m.group(1)
    total = re.search(r"(\d+) total", line)
    passed = re.search(r"(\d+) passed", line)
    failed = re.search(r"(\d+) failed", line)
    skipped = re.search(r"(\d+) (?:skipped|todo)", line)
    if not (total or passed):
        return None
    npass = int(passed.group(1)) if passed else 0
    nskip = int(skipped.group(1)) if skipped else 0
    ntot = int(total.group(1)) if total else npass + nskip
    return (ntot, failed is None, nskip)


def _parse_go(out):
    """Count tests, not packages.

    `go test ./...` prints one `ok <pkg>` line per package, so a package with
    twenty tests reads as one — a unit mismatch that would make every honest
    figure in the project look wrong. With -v, each test reports its own
    `--- PASS:` line; sub-tests are indented, so anchoring to column zero counts
    top-level tests only.
    """
    passed = len(re.findall(r"^--- PASS: ", out, re.M))
    failed = len(re.findall(r"^--- FAIL: ", out, re.M))
    skipped = len(re.findall(r"^--- SKIP: ", out, re.M))
    if not (passed or failed or skipped):
        return None
    return (passed + failed + skipped, failed == 0, skipped)


PARSERS = {"unittest": _parse_unittest, "pytest": _parse_pytest,
           "node": _parse_node, "go": _parse_go}


def _pytest_importable():
    try:
        return importlib.util.find_spec("pytest") is not None
    except Exception:
        return False


def run_suite(root):
    """Execute the project's suite. Returns (total, ok_flag, skipped, output) or None.

    A run that collected **zero tests is never a pass.** `python3 -m unittest` prints
    a cheerful `Ran 0 tests / OK` when it collects nothing — which is exactly what
    happens to pytest-style bare functions, since unittest only finds TestCase
    subclasses. Reading that as success let the ship gate certify a suite that
    executed nothing: the guarantee attesting to its own emptiness. Found in the
    first human-driven run, by the orchestrator, before any human noticed.

    So: if unittest collects nothing and pytest is importable, retry under pytest
    before concluding anything. If the total is still zero, the result is NOT ok,
    and callers are told collection failed rather than that the suite passed.
    """
    found = detect_suite(root)
    if not found:
        return None
    kind, argv = found

    def _run(kind, argv):
        try:
            p = subprocess.run(argv, cwd=str(root), capture_output=True,
                               text=True, timeout=600)
        except Exception as exc:
            return ("ERROR", False, 0, f"{' '.join(argv)}: {exc}")
        out = (p.stdout or "") + (p.stderr or "")
        parsed = PARSERS[kind](out)
        if parsed is None:
            return (None, p.returncode == 0, 0, out)
        total, passed, skipped = parsed
        return (total, passed, skipped, out)

    result = _run(kind, argv)

    # Zero collected under unittest is usually pytest-style tests, not an empty
    # project — a project with no test files at all never reaches here.
    if kind == "unittest" and result[0] == 0 and _pytest_importable():
        retry = _run("pytest", [sys.executable, "-m", "pytest", "-q"])
        if retry[0] not in (0, None, "ERROR"):
            return retry

    total, passed, skipped, out = result
    if total == 0:
        return (0, False, 0,
                out + "\n\nCOLLECTED ZERO TESTS. Test files exist but the runner "
                "matched none of them, so nothing was verified. A suite that "
                "executed nothing cannot certify anything.")
    return result


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
