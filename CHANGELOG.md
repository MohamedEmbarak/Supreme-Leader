<!-- truth-lint: historical -->
<!--
  A changelog records what was true of a release, not what is true of HEAD. The
  2.1.0 entry quotes `Ran 0 tests` because that figure IS the defect it describes;
  updating it to match the current suite would falsify the record rather than
  correct it. Marked at file level for that reason, and the marker stays greppable
  so the exemption is visible to the next auditor.
-->

# Changelog

## 2.2.0 — the guard speaks plainly, and covers npm

Prompted by an outside review that verified this plugin's claims independently before making
any. Everything below is either a defect it named or a gap it identified.

**The enforcement layer spoke lore in plain mode.** `truth-lint` announced `DOCTRINE §III`
and `silence-meter` announced `LAW OF SILENCE` — *"a subordinate's verbosity is the Supreme
Leader's shame"* — to projects that had asked for plain language. The root cause was worse
than the symptom: **no hook read the register at all.** `org_field` was called exactly once
in the codebase, for `MUSTER`. The mechanism was identical in both registers, as documented;
the voice was not, which is the same defect pointing the other way. Hooks now resolve the
register — session file first, then `ORGANIZATION.md`, defaulting to plain — and a test
asserts that no lore vocabulary reaches a plain-mode user.

**Fabricated npm packages are now blocked.** The Python guard has always caught its
equivalent; a hallucinated package in a `.ts` deliverable went straight through. That is the
more consequential fabrication of the two: unlike a wrong figure it survives review, and the
name an agent invents may be registered by someone else tomorrow. Any JS/TS file in
`deliverables/` importing a package that is neither declared in `package.json` nor present in
`node_modules` is refused. Static imports, `require`, dynamic `import()`, and function-local
requires are all caught. `tsconfig` path aliases, Node builtins, subpath imports, scoped
packages, and commented-out imports are not mistaken for dependencies — a guard that blocks
honest work gets switched off.

**The evidence ledger now holds evidence.** It recorded commands only, which meant an agent
could run the suite, watch three tests fail, and write "all green" with the ledger showing
nothing but `pytest -q`. It now records the tail of each result too, correlated by tool id,
and where `truth-lint` cannot re-run a suite it checks the claimed line against the ledger
instead — so a figure that appeared in no command output is named as unobserved rather than
passing unexamined. Pre- and post-tool records are kept separately, so a failing command
still leaves its attempt on the record.

**Line numbers in refusals were off by one** whenever a blank line preceded a pytest figure:
`^\s*` matches newlines even under `re.M`, so the match began on the blank line above.

**The three limits logged in 2.1.0 are addressed** at the prompt layer, where they live: the
orchestrator is told to dispatch and wait rather than poll a sub-agent that has nothing to
report, the ship gate's refusal now says not to restate the report it interrupted, and the
Genesis skeleton is a literal file rather than an annotated one, so its guidance can no
longer be transcribed into `ORGANIZATION.md`.

**A test that only passed because of its environment.** The zero-collection guard's test
asserted `not passed` unconditionally — true only where pytest is absent, which is why CI
never caught it. Both branches are now forced explicitly.

### Found by attacking the release rather than using it

Before tagging 2.2.0 the enforcement layer was attacked deliberately: forge the gates, poison
the ledger, smuggle fabrications past each guard, and trip false positives. Five findings,
all fixed here.

**The parser could be poisoned by a test docstring.** `unittest -v` echoes each test's
docstring, and the summary was read from the *first* `Ran N tests` in the stream. This
repository's own suite therefore reported **99 instead of 119** — one test's docstring quotes
`Ran 99 tests` while explaining that echoing a figure must not attest to it. A planted
docstring was enough to make the hook certify a number no run produced, which is precisely
the failure this project exists to prevent. The summary is now anchored to column zero and
read as the *last* match, and the verdict is taken from after the summary line so a verbose
per-test `ok` cannot stand in for it.

**QA-PASS and the ledger were forgeable by direct file write.** `gate.py` refuses to record
QA-PASS and the README said it "cannot be claimed by an agent at all" — true of the CLI,
false of the filesystem. Writing `.claude/sl/gate-QA-PASS.json` produced
`hook-verified: Ran 412, skipped 0` that no run justified, and because the directory is
gitignored the forgery never appears in a diff. 2.2 had made truth-lint *consult* the ledger,
which turned a passive log into something worth forging. A new `state-guard` hook refuses
Write and Edit into `.claude/sl/`. The residual — a shell redirect still lands — is stated in
the README rather than papered over.

**`truth-lint: historical` was honoured by the repo audit and ignored at write time.** The
documented escape hatch worked everywhere except where it is needed: an archive of a
completed decree could not be written at all. The pattern now lives in one place so the two
components cannot drift again.

**Workspace dependencies read as fabricated.** Only the root `package.json` was consulted, so
in a monorepo a dependency declared in `deliverables/web/package.json` was reported as
invented — a false positive in exactly the repo shape the npm guard was built for.

**Known ways past the guards are now published** in the README: files written via `Bash` skip
`truth-lint` entirely, paraphrased figures are invisible, declaring a fabricated package
defeats the npm check, Python dynamic imports are unchecked, and work outside `deliverables/`
is ungated. A guard whose limits are undocumented is one people over-trust.

**Found by the first live test of the release, on Windows:**

- **Test discovery walked into `.claude/worktrees/`** — the full second checkout the harness
  leaves behind. That produced the module name `.claude.worktrees.<id>.runs.…`, whose leading
  dot makes `__import__` read it as a relative import with no package, so unittest raised
  `ValueError: Empty module name` and **the entire suite failed to load** in a repository
  where every test passes. Gitignored, so invisible to anyone not on that machine.
- **A runner that never ran was reported as a failing suite.** With no summary to parse, the
  result was `passed=False`, and truth-lint announced *"claims the suite passes — actual: the
  suite does NOT pass"* about a repository whose tests all pass. That is a false accusation
  made by the hook that exists to prevent them, and worse than silence: it tells an agent to
  change a figure that was correct. No summary plus a non-zero exit now reports ERROR, and
  the hook says it could not check.

**Install docs now say to restart.** Hook commands resolve `${CLAUDE_PLUGIN_ROOT}` at session
start, so updating a plugin mid-session leaves the previous version's hooks running while the
manifest reports the new one. Both defects above were reported twice from a session executing
2.1.0 hooks against a 2.2.0 install, which is a confusing way to lose an afternoon.

**134 tests, 21 mutants.** Each mutant reintroduces a shipped defect and fails the build if
the guard does not catch it.

**Unresolved, and now measurable.** Whether five teams plus hooks beats one agent with the
same hooks and no organization has never been tested. The harness for testing it ships in
`experiments/baseline/` with no results in it — three arms, ten decrees, counting blocked
fabrications against tokens. The uncomfortable hypothesis is that the hooks carry the value
and the org chart carries the cost. That is worth knowing either way.

## 2.1.0 — the verifier learns to count

Found by running the organization against a real decree, not by reading the code.

**A green gate over nothing.** `unittest` prints `Ran 0 tests` followed by `OK` when it
collects nothing at all. A suite written as pytest-style bare functions matched none of its
patterns, and the ship gate certified the result: `QA-PASS: hook-verified: Ran 0, skipped 0`.
The run executed zero tests and the gate passed it, announcing the fact only in a note nobody
was obliged to read. Zero collection is now a failure with a stated reason, and where pytest
is importable the runner retries under it before concluding anything. This is the fix that
matters in this release; the run that exposed it is archived in
[TRY-SL](https://github.com/MohamedEmbarak/TRY-SL/tree/main/runs/loc_2026_08).

**Verification beyond Python.** Suite detection now reads `package.json` and `go.mod` before
sniffing files, and parses Node's TAP output (`# tests N`), jest's summary line, and
`go test -v` (counting `--- PASS:` lines, not packages). Each was checked against the real
tool: an earlier build assumed Node emitted jest's format and counted Go packages as tests.

**The gate stopped coaching a false pass.** Under a SKIRMISH muster the remedy text still
instructed the agent to record `BIZ-ACCEPT` — a gate that muster does not field. It now
instructs only what is required. An unset muster still resolves to FULL, erring toward more.

**Windows path separators** in the remedy lines now use the platform's own, via `os.fspath`.

**`/supreme-leader:verify`** runs the repo-wide claim audit on demand. Records that quote
historical figures can be exempted with a `truth-lint: historical` marker, which stays
greppable so exemptions remain visible rather than silent.

**The import guard ran on Python 3.10+ only.** `sys.stdlib_module_names` does not exist on
3.9, so the check raised `AttributeError` and exited 1 — which Claude Code treats as a hook
error, not a block. On that interpreter the fabricated-import guard was not failing loudly,
it was not running at all, while still appearing installed. Same shape as the zero-test gate.
Found by writing the test suite below.

**Corrected in `README.md`:** the evidence ledger was described as making observed output
checkable. It records the commands that ran, not their output. The QA-PASS note now also
names the interpreter that certified the run.

**Node verification never ran on Windows.** `detect_suite` returns `npm test`; on Windows
`npm` is `npm.cmd`, and `CreateProcess` will not launch a batch file from a bare name.
`subprocess` raised `FileNotFoundError`, the runner reported `ERROR`, and both hooks stand
down on `ERROR`. It failed safe — no gate was written, no false figure cleared — but the
guard was silently absent. `argv[0]` is now resolved through `shutil.which`, with batch
targets sent via `COMSPEC`. Found by the Windows CI leg below, the only place it is visible.

**The enforcement layer is now itself tested.** 85 tests over the four hooks and the gate
CLI, stdlib-only, run on Linux, Windows and macOS. A second CI job reintroduces each of the
nine defects listed here and requires the corresponding test to fail — a guard whose mutant
survives is decorative, and a green suite proves nothing until it can go red.

## 2.0.0 — the installable organization

- Restructured as a Claude Code plugin with a self-hosted marketplace: install with
  `/plugin marketplace add MohamedEmbarak/Supreme-Leader` then
  `/plugin install supreme-leader@embarak`.
- **Plain register is now the default.** The lore is an optional overlay via
  `/supreme-leader:lore on`. Mechanism identical in both registers.
- Enforcement hooks ship with the plugin: truth-lint (blocks test claims that do not
  reproduce and imports that do not resolve), ship-gate (hash-bound gates; QA-PASS is
  hook-written only), evidence-ledger, silence-meter. Hooks activate only when
  ORGANIZATION.md exists in the project; measured no-op overhead is under ~80ms.
- Lightweight defaults: five leads instead of a sixteen-agent Genesis (teams staff up on
  demand), SKIRMISH muster (Dev + QC) for small decrees, FULL pipeline for real builds.
- Commands: decree, report, roster, review, lore.

## 1.0.0 — the organization, complete

- The original prompt organization: doctrine, orchestrator persona, five directorate leads,
  protocols, writs, the Book of the Wiped, and a worked example run. Lore-register, prompt-only.
