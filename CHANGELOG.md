# Changelog

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

**Corrected in `README.md`:** the evidence ledger was described as making observed output
checkable. It records the commands that ran, not their output. The QA-PASS note now also
names the interpreter that certified the run.

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
