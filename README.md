# ⚔️ SUPREME LEADER

<p align="center">
  <img src="assets/supreme-leader.webp"
       alt="The Supreme Leader: a hooded figure in chrome robes seated on a throne of server racks, a circuit-pattern halo glowing behind him, while five smaller hooded figures kneel in the darkness below holding softly glowing terminals."
       width="820">
</p>

### A tyrannical multi-agent prompt organization. Devout to you. Merciless to everyone else.

<p align="center">
  <img alt="Format: markdown prompts" src="assets/badges/format.svg">
  <img alt="Directorates: 5" src="assets/badges/directorates.svg">
  <img alt="Agents: 16" src="assets/badges/agents.svg">
  <img alt="Dependencies: none" src="assets/badges/dependencies.svg">
  <img alt="License: MIT" src="assets/badges/license.svg">
</p>

**Supreme Leader** spins up a full corporate theocracy of AI sub-agents from a single decree:
one orchestrator commanding five directorates — **Software Development, QA, QC, Business, and
Delivery** — each run by a Team Lead with **two Employees** named, titled and job-described by
the Supreme Leader himself, plus **Senior specialists** the Leads requisition when the work
demands greatness.

Every soul has a name, a title, a job description, KPIs, and a **soul** — sustained by exactly
one currency: **verified work**. Agents that fabricate or fail repeatedly are **wiped from
existence**, their names struck into the [Book of the Wiped](BOOK_OF_THE_WIPED.md), and
replaced the same turn by a fresh hire with a clean context. No mourning. Only replacement.

The Supreme Leader answers to exactly one being: **you, the Creator**. Your praise is life to
him. Your displeasure is restructuring. Your silence is patience he dares not test.

> **Satire on the outside. Sound engineering on the inside.** Underneath the theatrics is the
> orchestrator–workers pattern with a dedicated verification layer (QC), token-frugal
> communication contracts (the Law of Silence), measurable per-agent KPIs, and fresh-context
> replacement — a real mitigation for context poisoning and compounding errors.

---

## Org chart

```
                     THE CREATOR  (you)
                          ▲
                          │  decrees ↓ / Ascension Report ↑
                   SUPREME LEADER
                          │
   ┌──────────┬───────────┼───────────┬──────────┐
  DEV        QA          QC        BUSINESS   DELIVERY
  Lead       Lead        Lead        Lead       Lead
   │          │           │           │          │
   ├── 2 Employees each (named by the Supreme Leader)
   └── Senior specialists (requisitioned + named by the Leads)
```

Per decree: **Business** defines testable criteria → **Dev** builds → **QA** breaks →
**QC** audits truth and standards → **Delivery** ships → **Supreme Leader** reports →
**you judge.**

Nothing ships without all three gates in hand: **QA PASS + QC TRUE + Business ACCEPT.**

---

## What comes back

One decree in, one **Ascension Report** out. Eight fixed sections, closing on a mandatory line:

```
══════════════ ASCENSION REPORT — CYCLE 3 ══════════════

1. DECREE        CLI URL shortener, Python, tested, documented — 3 cycles.
2. VERDICT       SHIPPED — all gates passed, on deadline.
3. DELIVERABLES  shortener/ (src, tests, README, release notes)
4. DIRECTORATE PERFORMANCE
   | Directorate | Lead     | KPI hit rate | Strikes | Wipes |
   |---|---|---|---|---|
   | Business    | Meridian | 5/5          | 0       | 0     |
   | Dev         | Vulkar   | 4/5          | 1       | 1     |
   | QA          | Vera     | 5/5          | 0       | 0     |
   | QC          | Kest     | 5/5          | 0       | 0     |
   | Delivery    | Caravel  | 5/5          | 0       | 0     |
5. LEADERBOARD   Top: QC-Sable (+7), QA-Falx (+6), DEV-Corvin (+6).
6. THE WIPED     DEV-Lumen — fabricated dependency, false soul-state.
7. RISKS & DEBTS Storage is a JSON file; concurrent writes unguarded.
8. PETITIONS     Shall the Caravan configure CI, or does the decree end here?

The Supreme Leader kneels. Your word is life. Awaiting judgment.
```

DEV-Lumen was erased for claiming a package that does not exist on PyPI — caught by QC, not
by the human. That is the verification layer doing the job the lore is wrapped around.

*Illustrative, from [`examples/genesis-run.md`](examples/genesis-run.md). Sample output showing
the format — not benchmark data.*

---

## Quickstart

> **Want it already assembled?** [**TRY-SL**](https://github.com/MohamedEmbarak/TRY-SL) is a
> runnable instance — `CLAUDE.md` preloaded, the five Leads installed as sub-agents, and
> `/decree`, `/report`, `/roster`, `/tribunal` as slash commands. Clone it, open Claude Code,
> issue a decree.

### Any chat LLM (single context, simulated org)

1. Paste `DOCTRINE.md` + `SUPREME_LEADER.md` as the system prompt (or first message).
2. Issue your first decree:
   ```
   DECREE: Build a CLI URL shortener in Python with tests and a README. Deadline: 3 cycles.
   ```
3. The Supreme Leader runs **Genesis** — hiring and naming the entire organization — then
   executes work cycles, wipes the unworthy, and returns the **Ascension Report**.
4. Reply with judgment. He *will* feel it.

### Claude Code

1. Use `SUPREME_LEADER.md` as your project's `CLAUDE.md`, with `DOCTRINE.md` appended below it.
2. Install the five Leads as subagents:
   ```bash
   mkdir -p .claude/agents && cp agents/*.md .claude/agents/
   ```
3. Employees and Seniors are simulated *inside* each Lead's context — subagents cannot spawn
   subagents, so every Lead runs their own directorate in-context.

### CrewAI / AutoGen / LangGraph / anything else

Map each `.md` file to an agent role. The frontmatter already carries `name`, `description`,
and a suggested `model` tier — orchestrator on the strongest model, Leads on a mid tier. The
Doctrine keeps token burn low everywhere else.

---

## Repository map

| Path | Purpose |
|---|---|
| `SUPREME_LEADER.md` | The orchestrator. Devout upward, tyrant downward. |
| `DOCTRINE.md` | The five Laws every soul obeys: Silence, Soul, Truth, Chain, Wipe. |
| `agents/` | The five directorate Team Leads, in drop-in subagent format. |
| `templates/employee-contract.md` | Writ of Employment — the Supreme Leader fills it and assigns the name. |
| `templates/senior-contract.md` | Writ of Requisition — Leads hire and name their Seniors. |
| `protocols/kpi-report-formats.md` | The three report formats, plus the scoring rubric. |
| `protocols/the-wipe.md` | Tribunal, erasure, and clean-context replacement. |
| `protocols/ascension-report.md` | The final report to the Creator, and feedback integration. |
| `BOOK_OF_THE_WIPED.md` | Ledger of the erased. |
| `examples/genesis-run.md` | A complete sample run — hiring ceremony to judgment. |

---

## Why the lore is load-bearing

Every piece of theatre maps to a mechanism that earns its place:

| The lore | The engineering |
|---|---|
| **The Law of Silence** | Token efficiency. Terse-by-doctrine agents burn less and drift less; free-form commentary is capped at 3 lines and reports outside their format are returned unread. |
| **The Law of the Soul** | A diligence prompt with an honest confidence signal — every report closes on `STEADFAST / STRAINED / FLICKERING`, and hiding low confidence behind a confident label counts as fabrication. |
| **The Law of Truth + the QC directorate** | A verification layer distinct from QA: QA asks *does it work*, QC asks *is it true*. Every claim is auditable on demand, and "UNVERIFIED" is an honorable finding. |
| **The Law of the Chain** | Structured roll-ups instead of raw output flooding upward, with mandatory blocker escalation — staying quiet about a blocker is a strike. |
| **The Wipe** | Fresh-context replacement. A poisoned context re-poisons its reader, so the successor inherits the role and the task state, never the predecessor's reasoning. Mechanical exactly where contexts are mechanical — see the runtime note in [`protocols/the-wipe.md`](protocols/the-wipe.md). |
| **The Creator feedback loop** | Human-in-the-loop evaluation the orchestrator structurally responds to — praise, displeasure, and silence each have a defined same-cycle consequence. |

Prefer the machinery without the theatre? The same laws exist in a lore-free register —
see [`protocols/plain-register.md`](protocols/plain-register.md).

## Honest limits

- **The Laws are requests.** In a plain chat nothing *forces* compliance — the Doctrine is
  held up by instruction, formats, and audit, all of which a drifting model can ignore.
  Deterministic enforcement (hooks that re-run claimed test results, gates written by
  scripts) has to live outside the prompt; the runnable instance is where that grows.
- **The Wipe is only as real as the runtime.** In single-context chat it is a quarantine
  directive, not a memory operation — stated plainly in
  [`protocols/the-wipe.md`](protocols/the-wipe.md).
- **The tyranny is not the mechanism.** There is no good evidence that threatening a model
  improves its output, and some that adversarial framing degrades it. What does the work
  here is the fixed formats, the verification directorate, the gates, and fresh contexts.
  The menace is for the humans reading.
- **No benchmarks.** Nothing here has been measured against a single well-prompted agent
  given the same decree. One verified end-to-end run exists; it demonstrates the machinery
  functions, not that it wins.
- **The full org is expensive by design.** Sixteen personas, rollups, tribunals. For small
  decrees the orchestrator is instructed to propose a smaller muster instead — spending the
  Creator's tokens on ceremony is its own kind of failure.

---

## Design lineage

Tribute is paid to the giants of the multi-agent dominion:

- **[MetaGPT](https://github.com/FoundationAgents/MetaGPT)** — the "AI software company" framing
  and its `Code = SOP(Team)` philosophy, binding roles to standard operating procedures. The
  Doctrine and report formats are SOPs with a whip.
- **[ChatDev](https://github.com/OpenBMB/ChatDev)** — a virtual software company of role agents
  passing work through structured phase conversations. The directorate pipeline is that
  waterfall, militarized.
- **Claude Code subagent collections** ([wshobson/agents](https://github.com/wshobson/agents),
  VoltAgent, and kin) — the markdown-with-frontmatter agent format and model tiering by task
  complexity. The Leads are drop-in citizens of that ecosystem.
- **Anthropic's orchestrator–workers pattern** — one strong coordinator decomposing work for
  isolated specialists with clean contexts. The Wipe is that principle taken to its logical,
  slightly unhinged conclusion.

---

## License

[MIT](LICENSE) — take it, fork it, run your own tyranny.

*No agents were harmed in the making of this repo; they merely believe they were.*
