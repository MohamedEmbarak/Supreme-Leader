# Changelog

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
