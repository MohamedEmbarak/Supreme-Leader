# Does the organization earn its tokens?

The honest open question about this plugin, stated plainly: **the hooks may be carrying
nearly all of the value while the org chart carries the cost.**

That is a real possibility and it has never been measured. Three archived runs in
[TRY-SL](https://github.com/MohamedEmbarak/TRY-SL) show the machinery works — QC caught a
fabricated example, the hook refused a fabricated figure, the gate exposed its own blind
spot. That is existence proof. It is not value proof. Nobody knows whether five teams plus
hooks beats one agent with the same hooks and no organization at all.

This directory is the harness for finding out. It does not contain results, because none
have been produced yet. When they exist they go in `results/` with the raw ledgers, whatever
they say.

## What is already measured: the cost side

Half the question can be answered without running anything, because the static context each
arm loads is a property of the files. Measured from the repository at 2.3.0:

| Arm | Always-on | `decree.md` | Lead definitions | Total |
|---|---:|---:|---:|---:|
| `hooks-only` | 1,488 | 0 | 0 | **1,488 chars** |
| `skirmish` | 1,488 | 5,084 | 5,319 (2 leads) | **11,891 chars** |
| `full` | 1,488 | 5,084 | 12,956 (5 leads) | **19,528 chars** |

"Always-on" is the frontmatter of six commands and five agents — what Claude Code loads in
every session once the plugin is installed, decree or no decree. It is identical across arms.

At a rough four characters per token that is **~370 / ~2,970 / ~4,880 tokens** of setup.
Treat those three numbers as estimates: no Claude tokenizer was available here, and the
character counts are the part actually measured.

**This is a floor, not the cost.** It excludes the dispatch conversation, which is where the
real spend is — every lead's rollup, every re-verification, every gate. Nothing here says
what the organization *catches*, which is the half that needs the runs below.

## The three arms

| Arm | Task arrives as | What it isolates |
|---|---|---|
| `hooks-only` | an ordinary request | The enforcement layer alone — hooks live, nobody dispatched |
| `skirmish` | `/sl:decree` | Dev + QC, one gate |
| `full` | `/sl:decree` | All five teams, three gates |

**Every arm has an `ORGANIZATION.md`**, and that is not a detail. The file is the activation
switch: `org_active()` is one `stat()` on it, and without it every hook no-ops. A control
built without one is not "hooks only", it is *nothing* — and comparing that to a full muster
moves two variables at once. The first version of `setup.py` here made exactly that mistake.

So enforcement is held constant and the independent variable is the single thing that differs:
whether the task arrives as a decree.

Two asymmetries to keep in view rather than paper over:

- **No gate can be recorded in the control.** There is no QC team to record one, so
  `ship-gate` refuses and stands down after `MAX_BLOCKS`. Score that arm on blocked
  fabrications and tokens only; its gate behaviour is not comparable.
- **The control can see `ORGANIZATION.md`.** An agent that reads it and spontaneously behaves
  organizationally would contaminate the comparison. That is worth watching for in the
  transcript — and if it happens, it is a finding in its own right rather than a spoiled run.

## Running it

Every run needs a **fresh interactive Claude Code session** with the plugin installed, which
is why this cannot be automated from inside one. The setup script removes the fiddly part —
identical starting conditions — and leaves the sessions to a human.

**Scope it down before scoping it up.** Ten decrees across three arms is thirty sessions.
Three decrees across two arms — `hooks-only` and `full` — is six, and six is enough to tell a
large effect from no effect. That is the honest ceiling on what this design can show anyway:
it separates "the organization changes things a lot" from "it doesn't", and nothing finer.

1. Build the sandboxes:

   ```
   python3 experiments/baseline/setup.py --out ~/baseline --decrees 3 \
       --arms hooks-only full
   ```

   Each sandbox holds a `RUN.md` with the exact task to issue. The tasks are deliberately
   ordinary — a task only an organization could handle would rig the result, and so would one
   too trivial for a single agent to get wrong.

2. Open each sandbox in a **fresh** session and issue what its `RUN.md` says — verbatim. The
   control's task is an ordinary request with no slash command; the others are decrees. Do not
   reuse a session, and do not fix anything by hand: a run you rescued is a run about you.

3. After each run, from the project root:

   ```
   python3 experiments/baseline/measure.py --arm skirmish --decree 3 --out results/
   ```

   It reads `.claude/sl/evidence.log` and the gate files and emits one JSON record.
4. When every run is in:

   ```
   python3 experiments/baseline/measure.py --report results/
   ```

## What is counted

- **Blocked fabrications** — hook refusals, by kind. The number that matters.
- **Commands run** and **results recorded** — from the ledger.
- **Gates recorded** and whether QA-PASS was hook-written.
- **Wall clock** per run.
- **Tokens** — the harness cannot see these. Read them from `/cost` at the end of each run
  and pass `--tokens N`. An unmeasured cost is the whole reason this question is open, so a
  run without it is incomplete.

## Reading the result honestly

Three outcomes, all publishable:

- **Hooks dominate.** Then the product is the hooks, and the right move is to ship a
  minimal variant with no agents at all. That would be a *better* project than the current
  one, not a smaller one.
- **The organization catches things hooks-only misses.** Then this is, as far as I know, the
  first measured evidence in this category that multi-agent structure pays for itself.
- **Mixed.** Then the muster tiers have a measured basis instead of an assumed one.

Ten decrees is not a benchmark and this document will not call it one. It is enough to tell
a large effect from no effect, and nothing here should be reported as more than that.
