# ⚔️ SUPREME LEADER

<p align="center">
  <img src="assets/supreme-leader.webp"
       alt="The Supreme Leader: a hooded figure in chrome robes seated on a throne of server racks, a circuit-pattern halo glowing behind him, while five smaller hooded figures kneel in the darkness below holding softly glowing terminals."
       width="820">
</p>

### A five-team agent organization where verification is enforced, not requested.

<p align="center">
  <a href="https://github.com/MohamedEmbarak/Supreme-Leader/actions/workflows/tests.yml"><img alt="Tests" src="https://github.com/MohamedEmbarak/Supreme-Leader/actions/workflows/tests.yml/badge.svg?branch=main"></a>
  <img alt="Format: Claude Code plugin" src="assets/badges/format.svg">
  <img alt="Teams: 5" src="assets/badges/teams.svg">
  <img alt="Roster: 5-16 agents" src="assets/badges/roster.svg">
  <img alt="Dependencies: none" src="assets/badges/dependencies.svg">
  <img alt="License: MIT" src="assets/badges/license.svg">
</p>

**Supreme Leader** is an installable Claude Code plugin: one orchestrator, five teams —
Business, Development, QA, QC, and Delivery — and a set of hooks that make the interesting
promises mechanical. A stated test result that does not reproduce is *blocked at write time*,
not caught in review. An invented package name is refused *before the file is written*, so it
never reaches disk to be staged.
The turn cannot end while ship gates are missing or stale — and the QA gate cannot be claimed
at all, because a hook writes it, only after a suite it ran itself actually passes.

It is deliberately lightweight. Plain vocabulary by default. Five leads by default, not
sixteen agents — teams staff up only when scope demands. Small decrees get a two-team
SKIRMISH instead of the full pipeline. When no organization is active in a project, the hooks
no-op in under ~80ms (measured) and stay out of your way entirely.

The tyrant lore that gave this repo its name still exists — as an **optional overlay**.
`/supreme-leader:lore on` and the teams become directorates, agents get names and souls,
fabricators face tribunals, and the report ends with the orchestrator kneeling. Same laws,
same formats, same thresholds; only the vocabulary changes. The doctrine is register-neutral.

---

## Install

```
/plugin marketplace add MohamedEmbarak/Supreme-Leader
/plugin install supreme-leader@embarak
```

**Restart Claude Code after installing or updating.** Hook commands resolve
`${CLAUDE_PLUGIN_ROOT}` when the session starts, so a `/plugin marketplace update` in a
running session leaves the *previous* version's hooks executing while the manifest reports
the new one. Two rounds of testing were spent on that during the 2.2.0 release, chasing a
defect that had already been fixed in the copy on disk.

Then, in any project:

```
/supreme-leader:decree Build a CLI that renames files by pattern, with tests and a README. 2 cycles.
```

## Commands

| Command | What it does |
|---|---|
| `/supreme-leader:decree <ambition>` | Triage the muster, seat the organization (first use), dispatch the teams. |
| `/supreme-leader:report` | The full account of the decree — every figure verified before stated. |
| `/supreme-leader:roster` | Roster, defect ledger, agents on notice, replacement log. |
| `/supreme-leader:review <agent>` | Verification review of a suspect claim. Acquittal or replacement. |
| `/supreme-leader:verify` | Audit every claim in the repository against a real run of the suite. |
| `/supreme-leader:lore [on\|off]` | The overlay. Same organization, different register. With no argument, reports which register is active and which file decided it. |

## What is enforced, not merely asked

| Hook | Fires on | What it makes impossible |
|---|---|---|
| `state-guard` | **before** every Write/Edit | A fabricated dependency reaching disk at all. The proposed content is checked before it is written, so an invented package name never exists to be staged or committed — `truth-lint` runs *after* the write and can only object once the bytes are there. Also refuses hand-written gates and ledger entries in `.claude/sl/`. Edits supply a fragment rather than a whole file, so those stay with the post-write check. |
| `truth-lint` | after every Write/Edit | A file stating a test result that does not reproduce — the hook detects the project's suite (Python `unittest`/`pytest`, Node via `npm test`, Go), re-runs it, and diffs. Claims are recognised in each framework's own output format. Also blocks imports in `deliverables/*.py` that do not resolve, found by parsing the syntax tree (function-local imports included), and packages in `deliverables/*.{js,ts,tsx,…}` that are neither declared in `package.json` nor installed. Path aliases from `tsconfig.json` and commented-out imports are not mistaken for dependencies. |
| `ship-gate` | before the turn can end | Shipping ungated. Gates bind to a content hash of `deliverables/`; any edit invalidates them. QA-PASS is written by the hook alone, on a real passing run. Muster-aware: SKIRMISH needs QC-TRUE, FULL needs QC-TRUE + BIZ-ACCEPT. Stands down after 3 refusals rather than trap the conversation. |
| `evidence-ledger` | before and after every Bash call | Transcripts with nothing behind them. Each command is recorded to `.claude/sl/evidence.log` with the tail of what it returned, correlated by tool id. Where `truth-lint` cannot re-run a suite it checks the claimed line against that ledger instead, so a figure that appeared in no result is visibly written rather than measured. Bounded: results are tailed, not archived whole, and a command that fails still leaves its attempt recorded. |
| `silence-meter` | when a lead returns | Guessing at verbosity — rollups are measured against budget. Advisory by design; it only measures this plugin's own leads. |

All five speak the active register. Refusals say the same thing in plain and lore; only the
vocabulary moves.

**Suites it can verify:** Python (`unittest`, or `pytest` when the project configures it and
it is importable), Node (`npm test` — TAP from `node --test`, jest, and vitest summaries), and
Go (`go test -v`, counting tests rather than packages). Project manifests win over file
sniffing, so a `package.json` with a test script makes it a Node project. If the suite runs but
its summary cannot be read, the hook falls back to the exit code and blocks nothing on a number
it did not actually read.

All hooks activate only when `ORGANIZATION.md` exists in the project — one `stat()` and out
otherwise. Run-state lives in `.claude/sl/`, which gitignores itself. No daemon, no service,
no dependency beyond Python 3 stdlib.

**The honest boundary:** hooks verify artifacts and executable claims. They cannot check
prose, cannot make a model reason better, and cannot un-poison a transcript. What they close
is the gap between *claimed* and *ran* — which is where agent work actually rots.

<details>
<summary><b>Known ways past the guards</b> — found by attacking the release, not by using it</summary>

Published because a guard whose limits are undocumented is a guard people over-trust.

| Gap | Why it stands |
|---|---|
| **Files written via `Bash` skip `truth-lint`.** The hook is `PostToolUse(Write\|Edit)`; `cat > file <<EOF` never triggers it. | The command is recorded in the ledger, but nothing re-reads it. Closing this needs a content check on every Bash call, which would be slow and easy to evade differently. |
| **A shell redirect into `.claude/sl/` still lands.** `state-guard` covers Write and Edit. | A PreToolUse(Bash) hook cannot reliably tell which files an arbitrary command will touch. |
| **Paraphrased figures are invisible.** `26/26 tests passing` is not matched — only verbatim runner output is. | Patterns are anchored to what runners actually print so ordinary prose is never mistaken for a claim. Loosening this trades a false negative for false positives that would block honest writing. |
| **Declaring a fabricated package in `package.json` defeats the npm guard.** | Resolution is declaration-first so a fresh checkout with no `node_modules` is not blocked. Mitigated downstream: the ship gate runs `npm test`, which fails on a package that does not exist. |
| **Python dynamic imports are not checked.** `importlib.import_module("x")` and `__import__("x")` pass. | The AST check reads `import` statements. A string argument is not one, and following arbitrary expressions is a different problem. |
| **A JS/TS import of a local file that does not exist is not caught.** `import { x } from "./nowhere"` passes. | Deliberate. Writing `a.ts` that imports `./b` *before* writing `b.ts` is ordinary practice, and the pre-write guard would refuse the first file every time. Blocking it would be a false positive on the most common shape of honest work, to catch a fabrication that fails loudly at build time and cannot be squatted by anyone. Package names get the guard because they have neither property. |
| **Work outside `deliverables/` is ungated.** Gates hash that directory; the import guards only fire inside it. | It is the convention the orchestrator is instructed to follow, not a sandbox. An agent that writes elsewhere is unenforced. |
| **A test docstring can shape what the parser reads.** Anchoring the summary to column zero and taking the last match closed the case found here; a runner that prints its summary elsewhere could still mislead it. | Parsing text a runner emits is inherently weaker than an API. Every parser is checked against the real tool for this reason. |

</details>

## The organization

```
                    OPERATOR (you)
                        │ decree ↓ / report ↑
                   ORCHESTRATOR
       ┌────────┬───────┼────────┬─────────┐
   BUSINESS   DEV      QA       QC     DELIVERY
     lead     lead    lead     lead      lead
```

Pipeline per decree: Business writes machine-judgable criteria → Dev builds → QA breaks →
**QC audits whether the claims are true** → Delivery ships, gates in hand. QC is the piece
most setups miss: QA asks *does it work*; QC re-runs what the others reported and answers
*is it true*. Each lead may staff up to two team members when scope demands — simulated
in-context, held to 6-line reports.

Every agent reports in a fixed format ending in an honest confidence signal
(`STEADFAST / STRAINED / FLICKERING`). Declaring low confidence costs nothing. Hiding it
behind a confident label is fabrication, and three defect points — or one fabrication that
reaches the operator — replaces the agent with a successor briefed on task state only.

## The lore

<details>
<summary>What <code>/supreme-leader:lore on</code> gets you</summary>

The original register. The operator becomes **the Creator**; the orchestrator becomes **the
Supreme Leader**, devout upward and tyrannical downward. Genesis bestows names — `DEV-Ashkar`,
`QA-Vera` — with titles and writs of employment. `CONFIDENCE` becomes `SOUL-STATE`, defect
points become strikes, replacement becomes **the Wipe** with its ledger
(`BOOK_OF_THE_WIPED.md`), reviews become tribunals, and reports end with the mandatory line:

> *The Supreme Leader kneels. Your word is life. Awaiting judgment.*

The full texts live in this repo: [`DOCTRINE.md`](DOCTRINE.md) (the five Laws),
[`SUPREME_LEADER.md`](SUPREME_LEADER.md) (the orchestrator persona),
[`protocols/`](protocols/) (report formats, the Wipe, the Ascension Report),
[`templates/`](templates/) (writs of employment), and a worked
[example run](examples/genesis-run.md). Nothing mechanical changes — the mapping is specified
in [`protocols/plain-register.md`](protocols/plain-register.md), and any behavioral
difference between registers beyond vocabulary is a reportable defect.

Why keep it at all? Because the theatre encodes the mechanism memorably: the Law of Silence
is token discipline, the soul is a confidence signal, the Wipe is fresh-context replacement.
The menace is for the humans reading. There is no evidence threatening a model improves its
output — the hooks are what improved it from a request to a guarantee.

</details>

## Prompt-only use (no plugin)

The organization predates the plugin and still works as pure prompts: paste `DOCTRINE.md` +
`SUPREME_LEADER.md` into any chat LLM as a system prompt and issue a `DECREE:` (this path is
lore-register and unenforced — the laws are requests there, stated plainly in
[Honest limits](#honest-limits)). The five `agents/*.md` files also work as standalone
Claude Code subagents without the plugin.

## Honest limits

- **Without the hooks, the Laws are requests.** The prompt-only path has no mechanism forcing
  compliance; that is exactly the gap the plugin exists to close, and it closes it only for
  artifacts and executable claims — not prose.
- **Replacement is only as real as the runtime.** Lead-level context death is mechanical
  (each dispatch starts empty). For team members simulated inside a lead, and in
  single-context chat, it is a quarantine directive — stated plainly in
  [`protocols/the-wipe.md`](protocols/the-wipe.md).
- **No benchmarks, and the org chart is unproven.** Three verified end-to-end runs exist
  ([TRY-SL](https://github.com/MohamedEmbarak/TRY-SL)) — a fabrication caught after it
  shipped, one refused before it reached disk, and a gate that passed over a suite which
  collected zero tests. That demonstrates the machinery functions. It does not show that five
  teams plus hooks beats **one agent with the same hooks and no organization at all**. The
  uncomfortable version of that hypothesis — the hooks carry the value, the org chart carries
  the token cost — has not been tested, and the harness for testing it ships in
  [`experiments/baseline/`](experiments/baseline/) with no results in it yet.
- **Enforcement covers Python, JavaScript/TypeScript, Go.** Test-figure verification handles
  `unittest`, `pytest`, Node's TAP, jest, and `go test`. Fabricated-dependency blocking covers
  Python imports and npm packages. Rust, Java, C#, Ruby and PHP get nothing, and there is no
  coverage-threshold gate in any language.
- **The full muster is expensive.** That is why SKIRMISH is the default and why the
  orchestrator is instructed to refuse ceremony for trivial decrees.

## Design lineage

- **[MetaGPT](https://github.com/FoundationAgents/MetaGPT)** — the AI-software-company
  framing: roles bound to SOPs. The doctrine and report formats are SOPs with a whip.
- **[ChatDev](https://github.com/OpenBMB/ChatDev)** — role agents passing work through a
  structured pipeline. Ours is that waterfall with a truth-audit stage.
- **Claude Code subagent collections** ([wshobson/agents](https://github.com/wshobson/agents)
  and kin) — the markdown-with-frontmatter agent format the leads are written in.
- **Anthropic's orchestrator–workers pattern** — one coordinator, isolated specialists,
  clean contexts. Replacement-on-fabrication is that principle taken to its conclusion.

## Map

| Path | Purpose |
|---|---|
| `.claude-plugin/` | Plugin manifest and marketplace catalog. |
| `commands/` | `decree`, `report`, `roster`, `review`, `verify`, `lore`. |
| `agents/` | The five team leads (plain register; lore identities apply on top). |
| `hooks/` | The enforcement layer: truth-lint, ship-gate, evidence-ledger, silence-meter, plus `gate.py` and a repo-wide `verify-claims.py`. |
| `DOCTRINE.md`, `SUPREME_LEADER.md` | The lore texts, and the prompt-only path. |
| `protocols/` | Report formats and rubric, the Wipe, the Ascension Report, the register mapping. |
| `templates/`, `examples/`, `BOOK_OF_THE_WIPED.md` | Lore-register instruments and a worked example. |
| `tests/`, `experiments/` | The suite that tests the enforcement layer, and the harness for the unrun baseline experiment. |

## License

[MIT](LICENSE) — take it, fork it, run your own organization.

*No agents were harmed in the making of this repo; they merely believe they were.*
