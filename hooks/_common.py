"""Shared helpers for the Supreme Leader enforcement hooks.

Design constraints, in order:

1. Honesty — a hook may only block on something it actually verified this run.
2. Weight — when no organization is active in the project, every hook must no-op
   in milliseconds. The check is one stat() on ORGANIZATION.md.
3. Containment — all run-state lives in .claude/sl/ inside the user's project,
   with a self-written .gitignore so it can never pollute their history.
"""

import ast
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


# sys.stdlib_module_names is 3.10+. On 3.9 the attribute is simply absent, and the
# import check raised AttributeError and died — exit 1, which Claude Code treats as a
# hook error rather than a block. The fabricated-import guard was therefore not
# failing loudly on 3.9; it was not running at all, while still appearing installed.
# The set is only a fast path: find_spec() resolves stdlib modules on its own, so the
# fallback is slower, not weaker.
STDLIB = frozenset(getattr(sys, "stdlib_module_names", ()) or sys.builtin_module_names)


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


def register(root):
    """PLAIN or LORE — the vocabulary this project is speaking.

    Two sources, because `/supreme-leader:lore` writes a session file while
    ORGANIZATION.md carries the committed default. The session file wins; a
    fresh clone falls back to the org file; absent both, PLAIN.

    Read directly rather than through state_dir(), which creates directories —
    a hook that decides what to *call* something must not have side effects.
    """
    f = root / ".claude" / "sl" / "register"
    try:
        if f.is_file():
            v = f.read_text(encoding="utf-8", errors="replace").strip().upper()
            if "LORE" in v:
                return "LORE"
            if "PLAIN" in v:
                return "PLAIN"
    except Exception:
        pass
    return "LORE" if "LORE" in org_field(root, "REGISTER", "").upper() else "PLAIN"


def phrase(root, plain, lore):
    """Pick the wording for the active register.

    The hooks used to speak lore unconditionally — `DOCTRINE §III`, `LAW OF
    SILENCE`, "the Supreme Leader's shame" — while the README promised plain by
    default since 2.0. Nothing read the register at all: org_field was called
    once in the codebase, for MUSTER. The mechanism was identical in both
    registers, as documented; the *voice* was not, which is the same defect in
    the other direction. Caught by an outside review, reproduced under an
    explicit `REGISTER: PLAIN`, and now tested.
    """
    return lore if register(root) == "LORE" else plain


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


# Typography that does not survive the trip to a Windows console. The hook writes
# UTF-8; a cp1252 terminal decodes it as U+FFFD, so every em dash in every refusal
# arrived as a black diamond — including in the line that says what was refused and
# why. A diagnostic that renders wrong on a common platform is a diagnostic that
# gets misread, and this one is the most important text the plugin ever prints.
# Prose can have nice dashes; a refusal cannot afford them.
_ASCII = {
    "—": "--",   # em dash
    "–": "-",    # en dash
    "…": "...",  # ellipsis
    "≤": "<=",
    "≥": ">=",
    "§": "Sec.",
    "‘": "'", "’": "'", "“": '"', "”": '"',
}


def asciify(text):
    for bad, good in _ASCII.items():
        text = text.replace(bad, good)
    return text.encode("ascii", "replace").decode("ascii")


def block(reason):
    print(asciify(reason), file=sys.stderr)
    sys.exit(2)


def ok(context=None, event=None):
    if context and event:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": event, "additionalContext": asciify(context)}}))
    sys.exit(0)


# --- test suite -----------------------------------------------------------------

# A file or line marked as a record of a past run rather than a live claim.
# Defined once and shared: truth-lint and verify-claims disagreeing about a
# documented marker is how the escape hatch came to work in the audit and not at
# write time. Deliberately explicit and greppable, so exemptions stay visible.
HISTORICAL = re.compile(r"truth-lint:\s*historical", re.I)

CLAIM_RAN = re.compile(r"\bRan\s+(\d+)\s+tests?\b")
CLAIM_OK = re.compile(r"^[^\S\n]*OK\b(?:[^\S\n]*\(skipped=(\d+)\))?[^\S\n]*$", re.M)
CLAIM_FAILED = re.compile(r"^[^\S\n]*FAILED\b", re.M)

# Reading a runner's own output is a different job from spotting a claim in prose,
# and conflating them was a way to fabricate a passing figure.
#
# `unittest -v` echoes each test's docstring, so any test whose documentation
# mentions a runner-shaped number puts that number into the stream ahead of the
# real summary. The parser took the first match and believed it: this repository's
# own suite reported 99 instead of 119, because one test's docstring quotes
# `Ran 99 tests` while explaining that echoing a figure must not attest to it.
# A planted docstring was therefore enough to make the hook certify a number no
# run produced — the precise failure this project exists to prevent.
#
# Both fixes are applied together: anchor to column zero, where unittest prints
# its summary and a docstring line never starts, and take the LAST match, since
# the summary is the final word by construction.
SUMMARY_RAN = re.compile(r"^Ran\s+(\d+)\s+tests?\b", re.M)
SUMMARY_OK = re.compile(r"^OK\b(?:\s*\(skipped=(\d+)\))?", re.M)


def _last(rx, text):
    m = None
    for m in rx.finditer(text):
        pass
    return m

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
# [^\S\n] is "horizontal whitespace": \s* would match newlines even under re.M,
# so a figure preceded by a blank line had its match start on the blank line and
# every reported line number was one too low.
CLAIM_PYTEST = re.compile(
    r"^[^\S\n]*(?=.*\b\d+ (?:passed|failed)\b)"
    r"(?:\d+ (?:passed|failed|skipped|error[s]?|xfailed|deselected)(?:, )?)+"
    r"(?: in [\d.]+s)?[^\S\n]*$", re.M)
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
            parts = f.relative_to(root).with_suffix("").parts
            # Anything under a dot-directory is not the project's test suite, and
            # its dotted name is not even importable: the harness leaves a full
            # second checkout in .claude/worktrees/, which produced the module
            # name `.claude.worktrees.<id>.runs.…`. A leading dot makes __import__
            # read it as a relative import with no package, so unittest raised
            # `ValueError: Empty module name` and the ENTIRE suite failed to load
            # — in a repository whose tests all pass. Found on a Windows machine
            # where that worktree existed; invisible here because it is gitignored.
            if any(p.startswith(".") for p in parts):
                continue
            if {"__pycache__", "node_modules", "site-packages", "build", "dist"} & set(parts):
                continue
            mods.append(".".join(parts))
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
    m = _last(SUMMARY_RAN, out)
    if not m:
        return None
    # Only the verdict that follows the summary counts. `-v` prints a lowercase
    # `ok` per test and a docstring may contain anything at all; the run's own
    # result is what unittest writes after the `Ran N tests` line.
    okm = _last(SUMMARY_OK, out[m.end():])
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


def resolve_argv(argv):
    """Resolve argv[0] to a real executable path before launching it.

    On Windows `npm` is `npm.cmd`, and CreateProcess will not launch a batch file
    from a bare name — subprocess raises FileNotFoundError. run_suite reported that
    as ERROR, and both hooks treat ERROR as "could not check" and stand down. So on
    Windows, Node test verification was not failing; it was not happening, while the
    plugin still reported itself as enforcing. Found by running the suite on a
    Windows runner, which is the only place it is visible.

    shutil.which() honours PATHEXT and finds the .cmd; a batch target then has to go
    through cmd.exe, which CreateProcess will not do implicitly. On POSIX this just
    yields an absolute path.
    """
    exe = shutil.which(argv[0])
    if exe is None:
        return argv  # let subprocess raise, and be reported honestly as ERROR
    if os.name == "nt" and exe.lower().endswith((".cmd", ".bat")):
        return [os.environ.get("COMSPEC", "cmd.exe"), "/c", exe, *argv[1:]]
    return [exe, *argv[1:]]


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
            p = subprocess.run(resolve_argv(argv), cwd=str(root), capture_output=True,
                               text=True, timeout=600)
        except Exception as exc:
            return ("ERROR", False, 0, f"{' '.join(argv)}: {exc}")
        out = (p.stdout or "") + (p.stderr or "")
        parsed = PARSERS[kind](out)
        if parsed is None:
            # No summary at all. A suite that merely fails still prints one
            # ("Ran N tests" then "FAILED"), so the absence of a summary together
            # with a non-zero exit means the runner never got as far as running
            # anything — an import error, a missing interpreter, a bad invocation.
            #
            # This used to return passed=False, and truth-lint duly announced
            # "claims the suite passes — actual: the suite does NOT pass" about a
            # repository whose tests all pass. That is a false accusation made by
            # the hook that exists to prevent them, and it is worse than staying
            # silent: it tells an agent to change a correct figure. Reporting
            # ERROR makes the hook say it could not check, which is the truth.
            if p.returncode != 0:
                return ("ERROR", False, 0, out)
            return (None, True, 0, out)
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


# --- JavaScript / TypeScript imports ---------------------------------------------

# Node's builtin modules. Hardcoded rather than shelled out to `node -p`, because
# this check must work in a project that has no Node installed at all — a .ts file
# can be written long before anyone runs it.
NODE_BUILTINS = frozenset("""
assert async_hooks buffer child_process cluster console constants crypto dgram
diagnostics_channel dns domain events fs http http2 https inspector module net os
path perf_hooks process punycode querystring readline repl stream string_decoder
sys timers tls trace_events tty url util v8 vm wasi worker_threads zlib
""".split())

JS_EXTENSIONS = frozenset({".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".mts", ".cts"})

_JS_LINE_COMMENT = re.compile(r"(?<![:'\"])//[^\n]*")
_JS_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.S)
# `from "x"`, `import "x"`, `export ... from "x"`, `require("x")`, `import("x")`.
_JS_IMPORT = re.compile(
    r"""(?:\bfrom\s*|\bimport\s*\(?\s*|\brequire\s*\(\s*|\bexport\s+\*\s+from\s*)"""
    r"""(['"])([^'"\n]+)\1""")


def js_specifiers(source):
    """Every module specifier a JS/TS file asks for, in source order.

    Comments are stripped first so a commented-out import is not treated as a
    dependency — blocking on one would be a false positive, and a linter that
    blocks honest work gets disabled.
    """
    text = _JS_BLOCK_COMMENT.sub(" ", source)
    text = _JS_LINE_COMMENT.sub(" ", text)
    out = []
    for m in _JS_IMPORT.finditer(text):
        spec = m.group(2).strip()
        if spec and spec not in out:
            out.append(spec)
    return out


def js_package_name(spec):
    """The installable package a specifier belongs to, or None if it is local.

    `lodash/get` is the lodash package; `@scope/pkg/sub` is `@scope/pkg`. Relative
    paths, absolute paths, URLs, and `#private` subpath imports are the project's
    own business and are never packages.
    """
    if not spec or spec[0] in "./#" or spec.startswith("~"):
        return None
    if "://" in spec or spec.startswith("data:"):
        return None
    if spec.startswith("node:"):
        return None
    parts = spec.split("/")
    if spec.startswith("@"):
        if len(parts) < 2:
            return None
        return "/".join(parts[:2])
    return parts[0]


def _deps_of(pkg):
    if not pkg.is_file():
        return set()
    try:
        data = json.loads(pkg.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return set()
    names = set()
    for field in ("dependencies", "devDependencies", "peerDependencies",
                  "optionalDependencies"):
        names.update((data.get(field) or {}).keys())
    return names


def _declared_js_deps(root, start=None):
    """Dependencies declared anywhere from the file's directory up to the root.

    Reading only the root manifest reported every workspace dependency as
    fabricated: in a monorepo the dependency belongs to `deliverables/web/
    package.json`, not the root. That is a false positive in exactly the repo
    shape this check was written for, and a guard that blocks honest work in a
    React or Next.js project gets switched off within the hour.
    """
    names = _deps_of(root / "package.json")
    if start is None:
        return names
    here = start if start.is_dir() else start.parent
    try:
        here.relative_to(root)
    except ValueError:
        return names
    while True:
        names |= _deps_of(here / "package.json")
        if here == root or here.parent == here:
            break
        here = here.parent
    return names


def _alias_prefixes(root):
    """TS/JS path aliases, so `@/components/Button` is not read as a package.

    A project that maps `@/*` to `src/*` is extremely common, and treating those
    as fabricated npm packages would block every honest file in a Next.js or Vite
    repo. Parsed leniently: tsconfig.json permits comments and trailing commas,
    which json.loads does not, so a parse failure falls back to a regex over the
    paths block rather than giving up and producing false positives.
    """
    prefixes = set()
    for name in ("tsconfig.json", "jsconfig.json"):
        f = root / name
        if not f.is_file():
            continue
        raw = f.read_text(encoding="utf-8", errors="replace")
        keys = []
        try:
            cleaned = _JS_BLOCK_COMMENT.sub(" ", raw)
            cleaned = _JS_LINE_COMMENT.sub(" ", cleaned)
            cleaned = re.sub(r",(\s*[}\]])", r"\1", cleaned)
            paths = ((json.loads(cleaned).get("compilerOptions") or {}).get("paths") or {})
            keys = list(paths.keys())
        except Exception:
            block = re.search(r'"paths"\s*:\s*\{(.*?)\}\s*[,}]', raw, re.S)
            if block:
                keys = re.findall(r'"([^"]+)"\s*:', block.group(1))
        for k in keys:
            prefixes.add(k.split("*")[0].rstrip("/") or k)
    return prefixes


def unresolved_py_imports(source, root):
    """Python imports in `source` that resolve to nothing. Raises SyntaxError.

    Takes text rather than a path so the same check can run on content that has
    not been written yet — a fabrication refused before it reaches disk beats one
    refused after, because the file is stageable either way.
    """
    mods = set()
    for node in ast.walk(ast.parse(source)):
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


def unresolved_js_imports(path, root, source=None):
    """Packages a JS/TS file imports that this project has not declared or installed.

    A hallucinated npm package is the most consequential fabrication an agent can
    commit to a JS project: unlike a wrong number it survives review, and the name
    it invents may be registered by someone else later. The Python guard has always
    caught its equivalent; until 2.2 a fabricated package in a .ts deliverable went
    straight through.

    Resolution is deliberately declaration-first: a package listed in package.json
    counts even when node_modules has never been installed, because an uninstalled
    dependency is a setup problem and blocking on it would make the hook useless in
    a fresh checkout.
    """
    if source is None:
        source = path.read_text(encoding="utf-8", errors="replace")
    declared = _declared_js_deps(root, path)
    aliases = _alias_prefixes(root)
    missing = []
    for spec in js_specifiers(source):
        if any(spec == a or spec.startswith(a.rstrip("/") + "/") for a in aliases):
            continue
        name = js_package_name(spec)
        if name is None or name in NODE_BUILTINS or name in declared:
            continue
        if any((d / "node_modules" / name).is_dir()
               for d in (root, *path.parents)):
            continue
        if name not in missing:
            missing.append(name)
    return missing


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


def ledger_attests(root, needle):
    """Was this exact text ever printed by a command the organization ran?

    The ledger records the tail of each result, which turns "this output was
    observed" from an assertion into a lookup. Used where the suite cannot be
    re-run: a figure present in a recorded tail was at least seen once, and one
    that appears nowhere was written rather than measured.

    Returns the timestamp of the earliest matching entry, or None.
    """
    p = root / ".claude" / "sl" / "evidence.log"
    if not needle.strip() or not p.is_file():
        return None
    try:
        with p.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                if rec.get("type") == "result" and needle in (rec.get("tail") or ""):
                    return rec.get("ts")
    except Exception:
        return None
    return None


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
