#!/usr/bin/env python3
"""The enforcement layer, tested.

A project whose entire claim is that verification beats diligence should not ask
to be taken on trust. Every defect this suite covers is one that actually shipped
and was found by running the thing, not by reading it:

  * `Ran 0 tests / OK` certified as a pass          (2.0.0, found mid-run)
  * Node's TAP output parsed as if it were jest's   (2.0.x, found against the real runner)
  * `go test ./...` counting packages as tests      (2.0.x, same)
  * BIZ-ACCEPT instructed under a SKIRMISH muster   (2.0.x)

Stdlib only, so it runs wherever the hooks do. Node and Go cases skip when the
toolchain is absent rather than failing — a missing runner is not a defect, and a
suite that cries wolf about its environment gets ignored.

    python3 -m unittest tests.test_hooks -v
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

HOOKS = Path(__file__).resolve().parent.parent / "hooks"
sys.path.insert(0, str(HOOKS))

import _common  # noqa: E402


# --- fixtures -------------------------------------------------------------------

PASSING_SUITE = """\
import unittest


class T(unittest.TestCase):
    def test_a(self):
        self.assertEqual(1, 1)

    def test_b(self):
        self.assertEqual(2, 2)
"""

FAILING_SUITE = """\
import unittest


class T(unittest.TestCase):
    def test_a(self):
        self.assertEqual(1, 2)
"""

# unittest collects TestCase subclasses only, so these are invisible to it.
# This is the exact shape that produced "Ran 0 tests / OK" in the loc run.
PYTEST_STYLE_SUITE = """\
def test_a():
    assert 1 == 1


def test_b():
    assert 2 == 2
"""

ORG_TEMPLATE = """\
# ORGANIZATION — LIVE STATE

**STATUS:** ACTIVE
**REGISTER:** {register}
**MUSTER:** {muster}
"""


class Project:
    """A throwaway project directory. `files` maps relative path -> contents."""

    def __init__(self, files=None, muster="FULL", register="PLAIN", org=True):
        self.files = files or {}
        self.muster = muster
        self.register = register
        self.org = org

    def __enter__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="sl-test-"))
        if self.org:
            self.write("ORGANIZATION.md",
                       ORG_TEMPLATE.format(muster=self.muster, register=self.register))
        for rel, body in self.files.items():
            self.write(rel, body)
        return self

    def __exit__(self, *exc):
        shutil.rmtree(self.dir, ignore_errors=True)

    def write(self, rel, body):
        p = self.dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        return p

    def hook(self, name, event=None):
        """Run a hook the way Claude Code runs it: JSON on stdin, exit code out.

        Returns (returncode, stdout, stderr). Exit 2 is the blocking contract.
        """
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.dir))
        p = subprocess.run(
            [sys.executable, str(HOOKS / name)],
            input=json.dumps(event or {}), capture_output=True, text=True,
            cwd=str(self.dir), env=env, timeout=300,
        )
        return p.returncode, p.stdout, p.stderr

    def gate_cli(self, *args):
        env = dict(os.environ, CLAUDE_PROJECT_DIR=str(self.dir))
        p = subprocess.run(
            [sys.executable, str(HOOKS / "gate.py"), *args],
            capture_output=True, text=True, cwd=str(self.dir), env=env, timeout=60)
        return p.returncode, p.stdout, p.stderr

    def read_gate(self, name):
        return _common.read_gate(self.dir, name)


def have(tool):
    return shutil.which(tool) is not None


# --- claim detection ------------------------------------------------------------

class ClaimDetection(unittest.TestCase):
    """What counts as a stated test figure, and what is merely prose."""

    def totals(self, text):
        return [(label, n) for label, n, _line in _common.claimed_totals(text)]

    def test_unittest_figure(self):
        self.assertEqual(self.totals("Ran 26 tests in 0.038s"), [("unittest", 26)])

    def test_singular_is_still_a_figure(self):
        self.assertEqual(self.totals("Ran 1 test in 0.0s"), [("unittest", 1)])

    def test_node_tap_figure(self):
        self.assertEqual(self.totals("# tests 3\n# pass 3\n"), [("node-tap", 3)])

    def test_jest_figure(self):
        self.assertEqual(
            self.totals("Tests:       1 failed, 9 passed, 10 total"), [("jest", 10)])

    def test_pytest_components_are_summed(self):
        self.assertEqual(self.totals("9 passed, 1 skipped in 0.12s"), [("pytest", 10)])

    def test_prose_is_not_a_figure(self):
        """The linter blocks writes. A false positive here stops honest work."""
        for line in ("all 12 review comments were addressed",
                     "we ran 26 experiments last quarter",
                     "Tests are documented in README.md",
                     "the suite is green"):
            with self.subTest(line=line):
                self.assertEqual(self.totals(line), [], f"prose matched: {line!r}")

    def test_line_numbers_are_reported(self):
        text = "intro\n\nRan 7 tests in 0.01s\n"
        self.assertEqual(_common.claimed_totals(text)[0][2], 3)

    def test_a_blank_line_does_not_shift_the_reported_line(self):
        """`^\\s*` matches newlines even under re.M, so the pytest pattern used to
        start its match on the preceding blank line and report every figure one
        line too high. The number in a refusal has to point at the actual line."""
        text = "## Verification\n\n9 passed, 1 skipped in 0.12s\n"
        self.assertEqual(_common.claimed_totals(text), [("pytest", 10, 3)])

    def test_multiple_figures_all_reported(self):
        text = "Ran 26 tests in 0.1s\n\nlater:\n\nRan 10 tests in 0.1s\n"
        self.assertEqual(self.totals(text), [("unittest", 26), ("unittest", 10)])


# --- suite parsers --------------------------------------------------------------

class Parsers(unittest.TestCase):
    """Each parser returns (total, passed, skipped). Formats taken from real runners."""

    def test_unittest_ok(self):
        self.assertEqual(
            _common._parse_unittest("Ran 10 tests in 0.007s\n\nOK\n"), (10, True, 0))

    def test_unittest_ok_with_skips(self):
        self.assertEqual(
            _common._parse_unittest("Ran 26 tests in 0.0s\n\nOK (skipped=1)\n"),
            (26, True, 1))

    def test_unittest_failure_is_not_a_pass(self):
        total, passed, _ = _common._parse_unittest("Ran 3 tests in 0.0s\n\nFAILED (failures=1)\n")
        self.assertEqual(total, 3)
        self.assertFalse(passed)

    def test_node_tap_is_not_read_as_jest(self):
        """`node --test` emits TAP. An earlier build assumed jest's format and
        silently found nothing to parse."""
        out = "# tests 3\n# suites 0\n# pass 3\n# fail 0\n# skipped 0\n"
        self.assertEqual(_common._parse_node(out), (3, True, 0))

    def test_node_tap_failure(self):
        out = "# tests 4\n# pass 3\n# fail 1\n# skipped 0\n"
        self.assertEqual(_common._parse_node(out), (4, False, 0))

    def test_jest_summary(self):
        out = "Tests:       1 failed, 9 passed, 10 total\nSnapshots:   0 total\n"
        self.assertEqual(_common._parse_node(out), (10, False, 0))

    def test_go_counts_tests_not_packages(self):
        """`go test ./...` prints one `ok <pkg>` line per package. Counting those
        made a package of twenty tests read as one."""
        out = ("=== RUN   TestA\n--- PASS: TestA (0.00s)\n"
               "=== RUN   TestB\n--- PASS: TestB (0.00s)\n"
               "=== RUN   TestC\n--- PASS: TestC (0.00s)\n"
               "PASS\nok  \texample\t0.002s\n")
        self.assertEqual(_common._parse_go(out), (3, True, 0))

    def test_go_subtests_do_not_inflate_the_count(self):
        """Sub-tests are indented; only column-zero entries are top-level tests."""
        out = ("--- PASS: TestA (0.00s)\n"
               "    --- PASS: TestA/case1 (0.00s)\n"
               "    --- PASS: TestA/case2 (0.00s)\n"
               "PASS\nok  \texample\t0.002s\n")
        self.assertEqual(_common._parse_go(out), (1, True, 0))

    def test_go_failure(self):
        out = "--- PASS: TestA (0.00s)\n--- FAIL: TestB (0.00s)\nFAIL\n"
        self.assertEqual(_common._parse_go(out), (2, False, 0))

    def test_pytest_sums_components(self):
        self.assertEqual(_common._parse_pytest("9 passed, 1 skipped in 0.1s"), (10, True, 1))

    def test_parsers_return_none_on_unrecognised_output(self):
        for name, parser in (("unittest", _common._parse_unittest),
                             ("node", _common._parse_node),
                             ("go", _common._parse_go),
                             ("pytest", _common._parse_pytest)):
            with self.subTest(parser=name):
                self.assertIsNone(parser("command not found\n"))


# --- suite detection and execution ----------------------------------------------

class SuiteDetection(unittest.TestCase):

    def test_python_suite_detected(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}) as p:
            kind, argv = _common.detect_suite(p.dir)
            self.assertEqual(kind, "unittest")
            self.assertIn("deliverables.test_x", argv)

    def test_manifest_beats_file_sniffing(self):
        """A repo with a package.json test script is a Node project even if it
        also vendors a Python helper with a test file beside it."""
        with Project({
            "package.json": '{"name":"x","scripts":{"test":"node --test"}}',
            "deliverables/test_x.py": PASSING_SUITE,
        }) as p:
            self.assertEqual(_common.detect_suite(p.dir)[0], "node")

    def test_go_module_detected(self):
        with Project({"go.mod": "module ex\n\ngo 1.21\n"}) as p:
            kind, argv = _common.detect_suite(p.dir)
            self.assertEqual(kind, "go")
            self.assertIn("-v", argv, "go must run verbose or tests cannot be counted")

    def test_no_suite_is_none_not_an_error(self):
        with Project({"README.md": "# hi\n"}) as p:
            self.assertIsNone(_common.detect_suite(p.dir))

    def test_launcher_is_resolved_to_a_real_executable(self):
        """On Windows `npm` is `npm.cmd`, which CreateProcess will not launch from
        a bare name. subprocess raised FileNotFoundError, run_suite reported ERROR,
        and both hooks stand down on ERROR — so Node verification was not failing
        on Windows, it was not running, while still reporting itself as enforcing.
        """
        if not have("npm"):
            self.skipTest("npm not installed")
        argv = _common.resolve_argv(["npm", "test", "--silent"])
        launcher = argv[0]
        self.assertTrue(os.path.isabs(launcher), f"argv[0] not resolved: {launcher}")
        self.assertTrue(os.path.exists(launcher), f"resolved to nothing: {launcher}")
        self.assertEqual(argv[-2:], ["test", "--silent"], "arguments must survive")
        if os.name == "nt":
            self.assertIn("/c", argv, "a .cmd target has to go through cmd.exe")

    def test_resolution_leaves_a_missing_tool_to_fail_honestly(self):
        argv = _common.resolve_argv(["definitely-not-a-real-tool-xyz", "-v"])
        self.assertEqual(argv, ["definitely-not-a-real-tool-xyz", "-v"])

    def test_pycache_is_not_a_test_module(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE,
                      "deliverables/__pycache__/test_stale.py": "junk"}) as p:
            argv = _common.detect_suite(p.dir)[1]
            self.assertNotIn("deliverables.__pycache__.test_stale", argv)


class SuiteExecution(unittest.TestCase):

    def test_passing_suite(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}) as p:
            total, passed, skipped, _ = _common.run_suite(p.dir)
            self.assertEqual((total, passed, skipped), (2, True, 0))

    def test_failing_suite(self):
        with Project({"deliverables/test_x.py": FAILING_SUITE}) as p:
            total, passed, _, _ = _common.run_suite(p.dir)
            self.assertEqual(total, 1)
            self.assertFalse(passed)

    def test_zero_collection_is_never_a_pass(self):
        """THE 2.1.0 DEFECT.

        `unittest` prints `Ran 0 tests` then `OK` when it matches nothing at all.
        Read as success, it let the ship gate certify a run that executed nothing:
        a guarantee attesting to its own emptiness.

        Both branches are forced rather than left to the environment. The original
        version of this test asserted `not passed` unconditionally, which is only
        true where pytest is absent — it passed in CI for that reason and failed
        the moment pytest appeared on the developer's machine. A test whose verdict
        depends on what happens to be installed is not testing the guarantee.
        """
        with Project({"deliverables/test_x.py": PYTEST_STYLE_SUITE}) as p:
            with unittest.mock.patch.object(_common, "_pytest_importable",
                                            return_value=False):
                total, passed, _, out = _common.run_suite(p.dir)
            self.assertEqual(total, 0, "unittest cannot collect bare functions")
            self.assertFalse(passed, "a suite that ran nothing must not pass")
            self.assertIn("COLLECTED ZERO TESTS", out,
                          "an empty collection must say so, not fail mutely")

    def test_pytest_rescues_a_suite_unittest_cannot_collect(self):
        """The other half: when pytest *is* available the run is retried under it,
        so a legitimate pytest-style suite is not reported as empty."""
        if not _common._pytest_importable():
            self.skipTest("pytest not importable by this interpreter")
        with Project({"deliverables/test_x.py": PYTEST_STYLE_SUITE}) as p:
            total, passed, _, _ = _common.run_suite(p.dir)
            self.assertEqual((total, passed), (2, True),
                             "the rescue must report the tests it actually ran")

    def test_node_suite_runs(self):
        if not have("npm") or not have("node"):
            self.skipTest("node/npm not installed")
        js = ("const test = require('node:test');\n"
              "const assert = require('node:assert');\n"
              "test('a', () => assert.ok(true));\n"
              "test('b', () => assert.ok(true));\n"
              "test('c', () => assert.ok(true));\n")
        with Project({
            "package.json": '{"name":"x","version":"1.0.0",'
                            '"scripts":{"test":"node --test deliverables/*.test.js"}}',
            "deliverables/x.test.js": js,
        }) as p:
            total, passed, _, _ = _common.run_suite(p.dir)
            self.assertEqual((total, passed), (3, True))

    def test_go_suite_runs(self):
        if not have("go"):
            self.skipTest("go not installed")
        go = ("package main\n\nimport \"testing\"\n\n"
              "func TestA(t *testing.T) {}\nfunc TestB(t *testing.T) {}\n")
        with Project({"go.mod": "module ex\n\ngo 1.21\n", "m_test.go": go}) as p:
            total, passed, _, _ = _common.run_suite(p.dir)
            self.assertEqual((total, passed), (2, True))


# --- deliverables hash ----------------------------------------------------------

class DeliverablesHash(unittest.TestCase):
    """Gates are bound to this hash. If it does not move when the work moves,
    a stale clearance rides on changed code."""

    def test_none_when_absent_or_empty(self):
        with Project({"README.md": "x"}) as p:
            self.assertIsNone(_common.deliverables_hash(p.dir))
            (p.dir / "deliverables").mkdir()
            self.assertIsNone(_common.deliverables_hash(p.dir))

    def test_stable_across_calls(self):
        with Project({"deliverables/a.py": "x = 1\n"}) as p:
            self.assertEqual(_common.deliverables_hash(p.dir),
                             _common.deliverables_hash(p.dir))

    def test_content_change_moves_the_hash(self):
        with Project({"deliverables/a.py": "x = 1\n"}) as p:
            before = _common.deliverables_hash(p.dir)
            p.write("deliverables/a.py", "x = 1\n\n")  # one blank line
            self.assertNotEqual(before, _common.deliverables_hash(p.dir))

    def test_new_file_moves_the_hash(self):
        with Project({"deliverables/a.py": "x = 1\n"}) as p:
            before = _common.deliverables_hash(p.dir)
            p.write("deliverables/b.py", "y = 2\n")
            self.assertNotEqual(before, _common.deliverables_hash(p.dir))

    def test_rename_moves_the_hash(self):
        """Paths are hashed as well as bytes; a pure rename is still a change."""
        with Project({"deliverables/a.py": "x = 1\n"}) as p:
            before = _common.deliverables_hash(p.dir)
            (p.dir / "deliverables" / "a.py").rename(p.dir / "deliverables" / "b.py")
            self.assertNotEqual(before, _common.deliverables_hash(p.dir))

    def test_pycache_is_ignored(self):
        """Byte-code churn must not invalidate a gate; only real work should."""
        with Project({"deliverables/a.py": "x = 1\n"}) as p:
            before = _common.deliverables_hash(p.dir)
            p.write("deliverables/__pycache__/a.cpython-311.pyc", "junk")
            self.assertEqual(before, _common.deliverables_hash(p.dir))


# --- organization state ---------------------------------------------------------

class OrganizationState(unittest.TestCase):

    def test_activation_switch(self):
        with Project({}, org=False) as p:
            self.assertFalse(_common.org_active(p.dir))
            p.write("ORGANIZATION.md", "**STATUS:** ACTIVE\n")
            self.assertTrue(_common.org_active(p.dir))

    def test_fields_are_read(self):
        with Project({}, muster="SKIRMISH", register="LORE") as p:
            self.assertEqual(_common.org_field(p.dir, "MUSTER"), "SKIRMISH")
            self.assertEqual(_common.org_field(p.dir, "REGISTER"), "LORE")

    def test_missing_field_returns_default(self):
        with Project({}) as p:
            self.assertEqual(_common.org_field(p.dir, "NOPE", "fallback"), "fallback")

    def test_state_dir_gitignores_itself(self):
        """Run-state is per-session. It must never reach a user's history."""
        with Project({}) as p:
            d = _common.state_dir(p.dir)
            self.assertEqual((d / ".gitignore").read_text().strip(), "*")


# --- gate.py --------------------------------------------------------------------

class GateCLI(unittest.TestCase):

    def test_qa_pass_cannot_be_recorded_by_hand(self):
        """The one gate an agent must never be able to assert about itself."""
        with Project({"deliverables/a.py": "x = 1\n"}) as p:
            rc, _, err = p.gate_cli("QA-PASS", "trust me")
            self.assertNotEqual(rc, 0)
            self.assertIn("cannot be recorded by hand", err)
            self.assertIsNone(p.read_gate("QA-PASS"))

    def test_qc_true_is_recorded_against_the_hash(self):
        with Project({"deliverables/a.py": "x = 1\n"}) as p:
            rc, _, _ = p.gate_cli("QC-TRUE", "ran the suite; 2/2 reproduced")
            self.assertEqual(rc, 0)
            self.assertEqual(p.read_gate("QC-TRUE")["deliverables"],
                             _common.deliverables_hash(p.dir))

    def test_a_gate_needs_a_stated_basis(self):
        with Project({"deliverables/a.py": "x = 1\n"}) as p:
            rc, _, err = p.gate_cli("QC-TRUE", "   ")
            self.assertNotEqual(rc, 0)
            self.assertIn("false PASS", err)

    def test_unknown_gate_rejected(self):
        with Project({"deliverables/a.py": "x = 1\n"}) as p:
            self.assertNotEqual(p.gate_cli("LGTM", "looks fine")[0], 0)

    def test_nothing_to_gate_when_deliverables_empty(self):
        with Project({}) as p:
            rc, _, err = p.gate_cli("QC-TRUE", "verified")
            self.assertNotEqual(rc, 0)
            self.assertIn("nothing to gate", err)


# --- ship-gate.py ---------------------------------------------------------------

class ShipGateMuster(unittest.TestCase):

    def required(self, muster):
        with Project({}, muster=muster) as p:
            import importlib.util
            spec = importlib.util.spec_from_file_location("sg", HOOKS / "ship-gate.py")
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod.required_gates(p.dir)

    def test_skirmish_fields_one_gate(self):
        self.assertEqual(self.required("SKIRMISH"), ["QC-TRUE"])

    def test_full_fields_both(self):
        self.assertEqual(self.required("FULL"), ["QC-TRUE", "BIZ-ACCEPT"])

    def test_unset_muster_errs_toward_more(self):
        """Fail-safe: an unwritten muster must not quietly drop a gate."""
        self.assertEqual(self.required("—"), ["QC-TRUE", "BIZ-ACCEPT"])


class ShipGate(unittest.TestCase):
    BLOCK = 2

    def test_noop_without_an_organization(self):
        """Weight: no organization, no involvement."""
        with Project({"deliverables/a.py": "x = 1\n"}, org=False) as p:
            self.assertEqual(p.hook("ship-gate.py")[0], 0)

    def test_noop_when_nothing_has_been_produced(self):
        with Project({}) as p:
            self.assertEqual(p.hook("ship-gate.py")[0], 0)

    def test_refuses_when_gates_are_missing(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}, muster="SKIRMISH") as p:
            rc, _, err = p.hook("ship-gate.py")
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("QC-TRUE: never recorded", err)

    def test_writes_qa_pass_itself_on_a_real_pass(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}, muster="SKIRMISH") as p:
            p.hook("ship-gate.py")
            gate = p.read_gate("QA-PASS")
            self.assertIsNotNone(gate, "the hook must record its own verification")
            self.assertIn("Ran 2", gate["note"])
            self.assertIn("via", gate["note"], "the certifying interpreter must be named")

    def test_refuses_a_failing_suite_and_writes_no_qa_pass(self):
        with Project({"deliverables/test_x.py": FAILING_SUITE}, muster="SKIRMISH") as p:
            rc, _, err = p.hook("ship-gate.py")
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("QA PASS DENIED", err)
            self.assertIsNone(p.read_gate("QA-PASS"))

    def test_refuses_a_suite_that_collected_nothing(self):
        """THE 2.1.0 DEFECT, at the gate rather than the parser."""
        with Project({"deliverables/test_x.py": PYTEST_STYLE_SUITE},
                     muster="SKIRMISH") as p:
            rc, _, err = p.hook("ship-gate.py")
            gate = p.read_gate("QA-PASS")
            if gate is not None:
                # pytest was importable and rescued the run; then it must be honest.
                self.assertNotIn("Ran 0", gate["note"])
            else:
                self.assertEqual(rc, self.BLOCK)
                self.assertIn("ZERO TESTS", err)

    def test_passes_when_the_required_gate_is_recorded(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}, muster="SKIRMISH") as p:
            p.gate_cli("QC-TRUE", "2/2 reproduced by command")
            self.assertEqual(p.hook("ship-gate.py")[0], 0)

    def test_full_muster_still_wants_business(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}, muster="FULL") as p:
            p.gate_cli("QC-TRUE", "2/2 reproduced by command")
            rc, _, err = p.hook("ship-gate.py")
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("BIZ-ACCEPT", err)

    def test_editing_deliverables_makes_a_gate_stale(self):
        """The clearance is for the code that was audited, not for its successor."""
        with Project({"deliverables/test_x.py": PASSING_SUITE}, muster="SKIRMISH") as p:
            p.gate_cli("QC-TRUE", "2/2 reproduced by command")
            self.assertEqual(p.hook("ship-gate.py")[0], 0)
            p.write("deliverables/test_x.py", PASSING_SUITE + "\n")
            rc, _, err = p.hook("ship-gate.py")
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("STALE", err)

    def test_remedy_instructs_only_the_gates_the_muster_fields(self):
        """A remedy naming BIZ-ACCEPT under SKIRMISH coaches the false PASS the
        hook exists to prevent."""
        with Project({"deliverables/test_x.py": PASSING_SUITE}, muster="SKIRMISH") as p:
            err = p.hook("ship-gate.py")[2]
            self.assertIn("QC-TRUE", err)
            self.assertNotIn("BIZ-ACCEPT", err)

    def test_remedy_paths_use_platform_separators(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}, muster="SKIRMISH") as p:
            err = p.hook("ship-gate.py")[2]
            self.assertIn(os.fspath(HOOKS / "gate.py"), err)

    def test_stands_down_rather_than_trapping_the_conversation(self):
        """A hook that cannot be escaped is worse than one that can be ignored."""
        with Project({"deliverables/test_x.py": FAILING_SUITE}, muster="SKIRMISH") as p:
            codes = [p.hook("ship-gate.py")[0] for _ in range(5)]
            self.assertEqual(codes[0], self.BLOCK)
            self.assertEqual(codes[-1], 0, "must downgrade to advisory, not block forever")


# --- truth-lint.py --------------------------------------------------------------

class TruthLint(unittest.TestCase):
    BLOCK = 2

    def event(self, path):
        return {"tool_name": "Write", "tool_input": {"file_path": str(path)}}

    def test_noop_without_an_organization(self):
        with Project({"NOTES.md": "Ran 999 tests\n\nOK\n"}, org=False) as p:
            self.assertEqual(p.hook("truth-lint.py", self.event(p.dir / "NOTES.md"))[0], 0)

    def test_blocks_a_figure_that_does_not_reproduce(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}) as p:
            notes = p.write("RELEASE_NOTES.md", "## Verification\n\nRan 14 tests\n\nOK\n")
            rc, _, err = p.hook("truth-lint.py", self.event(notes))
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("claims 14 tests", err)
            self.assertIn("actual: 2", err)

    def test_allows_the_figure_that_reproduces(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}) as p:
            notes = p.write("RELEASE_NOTES.md", "Ran 2 tests in 0.0s\n\nOK\n")
            self.assertEqual(p.hook("truth-lint.py", self.event(notes))[0], 0)

    def test_blocks_claiming_a_pass_the_suite_does_not_deliver(self):
        with Project({"deliverables/test_x.py": FAILING_SUITE}) as p:
            notes = p.write("RELEASE_NOTES.md", "Ran 1 test in 0.0s\n\nOK\n")
            rc, _, err = p.hook("truth-lint.py", self.event(notes))
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("does NOT pass", err)

    def test_says_so_when_there_is_no_suite_to_check_against(self):
        """Advisory, not a block: an unverifiable claim is not a proven false one."""
        with Project({}) as p:
            notes = p.write("NOTES.md", "Ran 5 tests\n\nOK\n")
            rc, out, _ = p.hook("truth-lint.py", self.event(notes))
            self.assertEqual(rc, 0)
            self.assertIn("UNVERIFIED", out)

    def test_a_file_making_no_claim_is_left_alone(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}) as p:
            notes = p.write("README.md", "# Project\n\nDoes a thing.\n")
            self.assertEqual(p.hook("truth-lint.py", self.event(notes))[0], 0)

    def test_blocks_an_import_that_does_not_resolve(self):
        with Project({}) as p:
            f = p.write("deliverables/a.py", "import definitely_not_a_real_pkg_xyz\n")
            rc, _, err = p.hook("truth-lint.py", self.event(f))
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("definitely_not_a_real_pkg_xyz", err)

    def test_catches_a_function_local_import(self):
        """Parsed from the syntax tree, not grepped from the file head."""
        with Project({}) as p:
            f = p.write("deliverables/a.py",
                        "def go():\n    import definitely_not_a_real_pkg_xyz\n    return 1\n")
            rc, _, err = p.hook("truth-lint.py", self.event(f))
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("definitely_not_a_real_pkg_xyz", err)

    def test_stdlib_and_local_imports_are_fine(self):
        with Project({}) as p:
            p.write("deliverables/helper.py", "def go():\n    return 1\n")
            f = p.write("deliverables/a.py",
                        "import os\nimport json\nfrom helper import go\n")
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], 0)

    def test_relative_imports_are_not_treated_as_packages(self):
        with Project({}) as p:
            p.write("deliverables/helper.py", "X = 1\n")
            f = p.write("deliverables/a.py", "from .helper import X\n")
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], 0)

    def test_unparseable_deliverable_is_blocked(self):
        with Project({}) as p:
            f = p.write("deliverables/a.py", "def broken(:\n")
            rc, _, err = p.hook("truth-lint.py", self.event(f))
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("does not parse", err)

    def test_import_check_is_scoped_to_deliverables(self):
        """Scratch files and experiments are not shipped work."""
        with Project({}) as p:
            f = p.write("scratch/a.py", "import definitely_not_a_real_pkg_xyz\n")
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], 0)

    def test_a_deleted_file_is_not_an_error(self):
        with Project({}) as p:
            self.assertEqual(
                p.hook("truth-lint.py", self.event(p.dir / "gone.md"))[0], 0)

    def test_import_check_survives_pythons_without_stdlib_module_names(self):
        """`sys.stdlib_module_names` is 3.10+. On 3.9 the check raised
        AttributeError and exited 1 — a hook error, not a block — so the
        fabricated-import guard was not running at all while still appearing
        installed. The same failure family as certifying a zero-test run.
        """
        with Project({}) as p:
            shim = p.dir / "_shim"
            shim.mkdir()
            (shim / "sitecustomize.py").write_text(
                "import sys\n"
                "try:\n    del sys.stdlib_module_names\n"
                "except AttributeError:\n    pass\n")
            env = dict(os.environ, CLAUDE_PROJECT_DIR=str(p.dir),
                       PYTHONPATH=str(shim))
            f = p.write("deliverables/a.py", "import os\nimport json\n")
            r = subprocess.run(
                [sys.executable, str(HOOKS / "truth-lint.py")],
                input=json.dumps(self.event(f)), capture_output=True, text=True,
                cwd=str(p.dir), env=env, timeout=300)
            self.assertNotIn("AttributeError", r.stderr)
            self.assertEqual(r.returncode, 0,
                             "stdlib imports must still resolve without the 3.10 set")

            bad = p.write("deliverables/b.py", "import definitely_not_a_real_pkg_xyz\n")
            r = subprocess.run(
                [sys.executable, str(HOOKS / "truth-lint.py")],
                input=json.dumps(self.event(bad)), capture_output=True, text=True,
                cwd=str(p.dir), env=env, timeout=300)
            self.assertEqual(r.returncode, self.BLOCK,
                             "the guard must still catch fabrications on 3.9")


# --- advisory hooks -------------------------------------------------------------

class EvidenceLedger(unittest.TestCase):

    def event(self, cmd):
        return {"tool_name": "Bash", "tool_input": {"command": cmd}}

    def test_records_the_command(self):
        with Project({}) as p:
            self.assertEqual(p.hook("evidence-ledger.py", self.event("ls -la"))[0], 0)
            log = (p.dir / ".claude" / "sl" / "evidence.log").read_text()
            self.assertEqual(json.loads(log.splitlines()[0])["cmd"], "ls -la")

    def test_appends_rather_than_replaces(self):
        with Project({}) as p:
            for c in ("ls", "pwd", "whoami"):
                p.hook("evidence-ledger.py", self.event(c))
            log = (p.dir / ".claude" / "sl" / "evidence.log").read_text()
            self.assertEqual(len(log.strip().splitlines()), 3)

    def test_never_blocks(self):
        with Project({}) as p:
            for event in ({}, {"tool_input": {}}, self.event("x" * 5000)):
                self.assertEqual(p.hook("evidence-ledger.py", event)[0], 0)

    def test_noop_without_an_organization(self):
        with Project({}, org=False) as p:
            p.hook("evidence-ledger.py", self.event("ls"))
            self.assertFalse((p.dir / ".claude" / "sl" / "evidence.log").exists())

    # --- 2.2: the ledger holds results, not just commands --------------------

    def result_event(self, tid, response):
        return {"hook_event_name": "PostToolUse", "tool_name": "Bash",
                "tool_use_id": tid, "tool_response": response}

    def records(self, p):
        text = (p.dir / ".claude" / "sl" / "evidence.log").read_text()
        return [json.loads(l) for l in text.splitlines() if l.strip()]

    def test_records_the_output_not_only_the_command(self):
        """Until 2.2 an agent could run the suite, watch it fail, and write
        'all green' — the ledger held the command and nothing about the result."""
        with Project({}) as p:
            p.hook("evidence-ledger.py",
                   {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                    "tool_use_id": "t1", "tool_input": {"command": "pytest -q"}})
            p.hook("evidence-ledger.py",
                   self.result_event("t1", {"stdout": "3 failed, 6 passed\n"}))
            recs = self.records(p)
            self.assertEqual([r["type"] for r in recs], ["cmd", "result"])
            self.assertIn("3 failed", recs[1]["tail"])
            self.assertEqual(recs[0]["tool_use_id"], recs[1]["tool_use_id"],
                             "the two halves must be correlatable")

    def test_tool_response_shape_is_read_defensively(self):
        """The harness types tool_response as `unknown`, so its shape is not a
        contract this hook may assume."""
        shapes = [
            ("plain string", "Ran 9 tests"),
            ("stdout dict", {"stdout": "Ran 9 tests", "stderr": ""}),
            ("stderr only", {"stdout": "", "stderr": "Ran 9 tests"}),
            ("content list", {"content": [{"type": "text", "text": "Ran 9 tests"}]}),
            ("bare list", ["Ran 9 tests"]),
        ]
        for label, response in shapes:
            with self.subTest(shape=label):
                with Project({}) as p:
                    rc, _, err = p.hook("evidence-ledger.py",
                                        self.result_event("t", response))
                    self.assertEqual(rc, 0, err[:200])
                    self.assertIn("Ran 9 tests", self.records(p)[0]["tail"])

    def test_a_result_is_digested_as_well_as_tailed(self):
        with Project({}) as p:
            p.hook("evidence-ledger.py", self.result_event("t", {"stdout": "hello"}))
            rec = self.records(p)[0]
            self.assertEqual(rec["bytes"], 5)
            self.assertTrue(rec["sha256"])

    def test_ledger_attests_finds_observed_output(self):
        with Project({}) as p:
            p.hook("evidence-ledger.py",
                   self.result_event("t", {"stdout": "9 passed, 1 skipped in 0.12s\n"}))
            self.assertTrue(_common.ledger_attests(p.dir, "9 passed, 1 skipped in 0.12s"))
            self.assertIsNone(_common.ledger_attests(p.dir, "47 passed"))

    def test_ledger_attests_ignores_commands(self):
        """Running `echo 'Ran 99 tests'` must not attest to the figure — only
        what a command *returned* is evidence, not what it was asked to do."""
        with Project({}) as p:
            p.hook("evidence-ledger.py",
                   {"hook_event_name": "PreToolUse", "tool_name": "Bash",
                    "tool_use_id": "t", "tool_input": {"command": "echo 'Ran 99 tests'"}})
            self.assertIsNone(_common.ledger_attests(p.dir, "Ran 99 tests"))

    def test_an_empty_result_is_not_recorded(self):
        with Project({}) as p:
            p.hook("evidence-ledger.py", self.result_event("t", {"stdout": ""}))
            log = p.dir / ".claude" / "sl" / "evidence.log"
            self.assertFalse(log.exists() and log.read_text().strip())


class LedgerBackedClaims(unittest.TestCase):
    """Where the suite cannot be re-run, the ledger is the fallback: a figure
    present in a recorded result was at least observed once, and one that
    appears nowhere was written rather than measured. Advisory either way —
    unverifiable is not the same as proven false."""

    def event(self, path):
        return {"tool_name": "Write", "tool_input": {"file_path": str(path)}}

    def context(self, p, path):
        out = p.hook("truth-lint.py", self.event(path))[1]
        try:
            return json.loads(out)["hookSpecificOutput"]["additionalContext"]
        except Exception:
            return out

    def ledger(self, text):
        return {".claude/sl/evidence.log": json.dumps(
            {"type": "result", "ts": "2026-08-12T06:40:00Z", "tail": text}) + "\n"}

    def test_a_figure_in_the_ledger_is_reported_as_observed(self):
        with Project(self.ledger("9 passed, 1 skipped in 0.12s\n")) as p:
            f = p.write("NOTES.md", "## Verification\n\n9 passed, 1 skipped in 0.12s\n")
            self.assertIn("evidence ledger", self.context(p, f))

    def test_a_figure_absent_from_the_ledger_is_named(self):
        with Project(self.ledger("9 passed, 1 skipped in 0.12s\n")) as p:
            f = p.write("NOTES.md", "## Verification\n\n47 passed in 0.9s\n")
            ctx = self.context(p, f)
            self.assertIn("does not appear", ctx)
            self.assertIn("47", ctx)

    def test_it_stays_advisory(self):
        """Blocking on unverifiable would stop honest work in any project this
        hook cannot execute."""
        with Project({}) as p:
            f = p.write("NOTES.md", "Ran 99 tests\n\nOK\n")
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], 0)


class SilenceMeter(unittest.TestCase):
    """Advisory by necessity: on SubagentStop, exit 2 makes the sub-agent *continue*,
    which for a verbosity complaint would produce more text, not less."""

    def event(self, agent, lines):
        return {"agent_type": agent,
                "last_assistant_message": "\n".join(f"line {i}" for i in range(lines))}

    def test_does_not_block_even_far_over_budget(self):
        with Project({}) as p:
            rc, out, _ = p.hook("silence-meter.py", self.event("qa-lead", 500))
            self.assertEqual(rc, 0, "blocking here would make the agent keep talking")
            self.assertIn("REPORT LENGTH", out)

    def test_quiet_when_within_budget(self):
        with Project({}) as p:
            rc, out, _ = p.hook("silence-meter.py", self.event("qa-lead", 5))
            self.assertEqual(rc, 0)
            self.assertNotIn("REPORT LENGTH", out)

    def test_ignores_agents_that_are_not_ours(self):
        with Project({}) as p:
            rc, out, _ = p.hook("silence-meter.py", self.event("some-other-agent", 500))
            self.assertEqual(rc, 0)
            self.assertNotIn("LAW OF SILENCE", out)

    def test_measurement_is_recorded(self):
        with Project({}) as p:
            p.hook("silence-meter.py", self.event("qc-lead", 100))
            entry = json.loads(
                (p.dir / ".claude" / "sl" / "verbosity.log").read_text().splitlines()[0])
            self.assertEqual(entry["lines"], 100)
            self.assertTrue(entry["over"])


# --- register -------------------------------------------------------------------

# Vocabulary that belongs to the lore overlay. None of it may reach a user who
# has not asked for it. Kept as data so the assertion is one loop, not a habit
# each new message has to remember.
LORE_WORDS = ("DOCTRINE", "LAW OF SILENCE", "Supreme Leader", "directorate",
              "Wipe", "strike", "tribunal", "kneel")


class Register(unittest.TestCase):
    """Plain is the default and lore is an overlay — including in the hooks.

    Until 2.2 nothing in the enforcement layer read the register at all:
    `org_field` was called once in the whole codebase, for MUSTER. The hooks
    announced `DOCTRINE §III` and `LAW OF SILENCE` to projects that had asked
    for plain language. The mechanism was identical in both registers, as
    documented; the voice was not.
    """

    def test_default_is_plain(self):
        with Project({}, org=False) as p:
            self.assertEqual(_common.register(p.dir), "PLAIN")

    def test_org_file_selects_lore(self):
        with Project({}, register="LORE") as p:
            self.assertEqual(_common.register(p.dir), "LORE")

    def test_session_file_overrides_the_org_file(self):
        """`/supreme-leader:lore` writes a session file; it must win."""
        with Project({".claude/sl/register": "LORE\n"}, register="PLAIN") as p:
            self.assertEqual(_common.register(p.dir), "LORE")
        with Project({".claude/sl/register": "PLAIN\n"}, register="LORE") as p:
            self.assertEqual(_common.register(p.dir), "PLAIN")

    def test_unreadable_register_falls_back_to_plain(self):
        with Project({".claude/sl/register": "gibberish\n"}) as p:
            self.assertEqual(_common.register(p.dir), "PLAIN")

    def test_reading_the_register_creates_nothing(self):
        """A function that decides what to *call* something must not have
        side effects; state_dir() would create .claude/sl on the way past."""
        with Project({}, org=False) as p:
            _common.register(p.dir)
            self.assertFalse((p.dir / ".claude").exists())

    def _block_output(self, project):
        notes = project.write("NOTES.md", "Ran 47 tests\n\nOK\n")
        return project.hook(
            "truth-lint.py",
            {"tool_input": {"file_path": str(notes)}})[2]

    def test_refusals_are_plain_by_default(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}, register="PLAIN") as p:
            err = self._block_output(p)
            self.assertIn("UNVERIFIED TEST CLAIM BLOCKED", err)
            for word in LORE_WORDS:
                self.assertNotIn(word, err, f"lore word {word!r} leaked into plain mode")

    def test_refusals_speak_lore_when_asked(self):
        with Project({"deliverables/test_x.py": PASSING_SUITE}, register="LORE") as p:
            self.assertIn("DOCTRINE", self._block_output(p))

    def test_the_refusal_itself_is_identical_in_both_registers(self):
        """Vocabulary may move. The verdict may not."""
        for reg in ("PLAIN", "LORE"):
            with Project({"deliverables/test_x.py": PASSING_SUITE}, register=reg) as p:
                notes = p.write("NOTES.md", "Ran 47 tests\n\nOK\n")
                rc, _, err = p.hook("truth-lint.py",
                                    {"tool_input": {"file_path": str(notes)}})
                self.assertEqual(rc, 2, f"{reg}: must still block")
                self.assertIn("claims 47 tests", err, f"{reg}: same finding")

    def test_advisories_are_plain_by_default(self):
        with Project({}) as p:
            out = p.hook("silence-meter.py", {
                "agent_type": "qa-lead",
                "last_assistant_message": "\n".join(f"l{i}" for i in range(200)),
            })[1]
            for word in LORE_WORDS:
                self.assertNotIn(word, out, f"lore word {word!r} leaked into plain mode")


# --- JavaScript / TypeScript imports ---------------------------------------------

class JsSpecifierParsing(unittest.TestCase):

    def test_every_import_form_is_found(self):
        src = """
        import fs from "node:fs";
        import { a } from 'pkg-a';
        import 'side-effect-pkg';
        export { b } from "pkg-b";
        export * from "pkg-c";
        const c = require("pkg-d");
        const d = await import("pkg-e");
        """
        found = _common.js_specifiers(src)
        for spec in ("node:fs", "pkg-a", "side-effect-pkg", "pkg-b", "pkg-c",
                     "pkg-d", "pkg-e"):
            self.assertIn(spec, found)

    def test_commented_out_imports_are_not_dependencies(self):
        """A false positive here blocks honest work, and a linter that blocks
        honest work gets switched off."""
        src = ('// import { x } from "line-comment-pkg";\n'
               '/* import { y } from "block-comment-pkg"; */\n'
               'import { z } from "real-pkg";\n')
        self.assertEqual(_common.js_specifiers(src), ["real-pkg"])

    def test_package_name_extraction(self):
        cases = {
            "lodash": "lodash",
            "lodash/get": "lodash",
            "@tanstack/react-query": "@tanstack/react-query",
            "@scope/pkg/deep/path": "@scope/pkg",
        }
        for spec, expected in cases.items():
            with self.subTest(spec=spec):
                self.assertEqual(_common.js_package_name(spec), expected)

    def test_non_packages_are_recognised(self):
        for spec in ("./local", "../up", "/abs", "#private", "~/alias",
                     "node:fs", "https://esm.sh/x", "data:text/js,1"):
            with self.subTest(spec=spec):
                self.assertIsNone(_common.js_package_name(spec))


class JsImportGuard(unittest.TestCase):
    """A hallucinated npm package is the most durable fabrication an agent can
    commit: unlike a wrong figure it survives review, and the name it invents
    may be registered by someone else tomorrow."""

    BLOCK = 2
    PKG = '{"name":"app","dependencies":{"lodash":"^4","@tanstack/react-query":"^5"}}'

    def event(self, path):
        return {"tool_name": "Write", "tool_input": {"file_path": str(path)}}

    def test_blocks_a_package_that_is_neither_declared_nor_installed(self):
        with Project({"package.json": self.PKG}) as p:
            f = p.write("deliverables/a.ts", 'import { x } from "react-hyper-forms";\n')
            rc, _, err = p.hook("truth-lint.py", self.event(f))
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("react-hyper-forms", err)

    def test_declared_dependencies_pass_without_node_modules(self):
        """An uninstalled dependency is a setup problem, not a fabrication —
        blocking on it would make the hook useless in a fresh checkout."""
        with Project({"package.json": self.PKG}) as p:
            f = p.write("deliverables/a.ts",
                        'import { get } from "lodash/get";\n'
                        'import { useQuery } from "@tanstack/react-query";\n')
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], 0)

    def test_installed_but_undeclared_package_passes(self):
        with Project({"package.json": self.PKG,
                      "node_modules/react/package.json": '{"name":"react"}'}) as p:
            f = p.write("deliverables/a.tsx", 'import React from "react";\n')
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], 0)

    def test_node_builtins_pass(self):
        with Project({"package.json": self.PKG}) as p:
            f = p.write("deliverables/a.js",
                        'import fs from "node:fs";\nconst path = require("path");\n')
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], 0)

    def test_tsconfig_path_aliases_are_not_packages(self):
        """`@/components/Button` is a path alias in most React projects. Reading
        it as a package would block every honest file in a Next.js repo."""
        tsconfig = ('{ // comments and trailing commas are legal here\n'
                    '  "compilerOptions": { "paths": { "@/*": ["src/*"] }, },\n}\n')
        with Project({"package.json": self.PKG, "tsconfig.json": tsconfig}) as p:
            f = p.write("deliverables/a.tsx", 'import B from "@/components/Button";\n')
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], 0)

    def test_relative_imports_pass(self):
        with Project({"package.json": self.PKG}) as p:
            f = p.write("deliverables/a.ts", 'import { x } from "./sibling";\n')
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], 0)

    def test_catches_a_require_inside_a_function(self):
        with Project({"package.json": self.PKG}) as p:
            f = p.write("deliverables/a.js",
                        'function load() {\n  return require("ghost-pkg-xyz");\n}\n')
            rc, _, err = p.hook("truth-lint.py", self.event(f))
            self.assertEqual(rc, self.BLOCK)
            self.assertIn("ghost-pkg-xyz", err)

    def test_scoped_fabrication_is_reported_whole(self):
        with Project({"package.json": self.PKG}) as p:
            f = p.write("deliverables/a.ts", 'import x from "@acme/not-real/sub";\n')
            err = p.hook("truth-lint.py", self.event(f))[2]
            self.assertIn("@acme/not-real", err)
            self.assertNotIn("@acme/not-real/sub", err)

    def test_guard_is_scoped_to_deliverables(self):
        with Project({"package.json": self.PKG}) as p:
            f = p.write("scratch/a.ts", 'import x from "ghost-pkg-xyz";\n')
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], 0)

    def test_a_project_with_no_package_json_still_blocks_fabrications(self):
        with Project({}) as p:
            f = p.write("deliverables/a.ts", 'import x from "ghost-pkg-xyz";\n')
            self.assertEqual(p.hook("truth-lint.py", self.event(f))[0], self.BLOCK)


# --- resilience -----------------------------------------------------------------

class Resilience(unittest.TestCase):
    """A hook that crashes on malformed input blocks the user's turn for no reason."""

    HOOK_EVENTS = [
        ("truth-lint.py", "PostToolUse"),
        ("ship-gate.py", "Stop"),
        ("evidence-ledger.py", "PreToolUse"),
        ("silence-meter.py", "SubagentStop"),
    ]

    def test_malformed_input_never_crashes_a_hook(self):
        with Project({}) as p:
            for hook, _ in self.HOOK_EVENTS:
                for event in ({}, {"tool_input": None}, {"tool_input": {"file_path": ""}}):
                    with self.subTest(hook=hook, event=event):
                        rc, _, err = p.hook(hook, event)
                        self.assertIn(rc, (0, 2), f"{hook} crashed: {err[:200]}")
                        self.assertNotIn("Traceback", err)

    def test_hooks_survive_an_unreadable_organization_file(self):
        with Project({}) as p:
            (p.dir / "ORGANIZATION.md").write_bytes(b"\xff\xfe\x00binary")
            for hook, _ in self.HOOK_EVENTS:
                with self.subTest(hook=hook):
                    rc, _, err = p.hook(hook, {})
                    self.assertIn(rc, (0, 2))
                    self.assertNotIn("Traceback", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
