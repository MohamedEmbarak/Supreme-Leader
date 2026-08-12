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

**119 tests, 16 mutants.** Each mutant reintroduces a shipped defect and fails the build if
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
