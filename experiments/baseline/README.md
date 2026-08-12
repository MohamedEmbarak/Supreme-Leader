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

## The three arms

| Arm | Setup | What it isolates |
|---|---|---|
| `hooks-only` | Plugin installed, **no `ORGANIZATION.md`**, plain Claude Code | The enforcement layer alone |
| `skirmish` | `ORGANIZATION.md` with `MUSTER: SKIRMISH` | Dev + QC, one gate |
| `full` | `ORGANIZATION.md` with `MUSTER: FULL` | All five teams, three gates |

The hooks are active in all three. That is the point: the variable under test is the
organization, not the enforcement.

Note the asymmetry — in `hooks-only` the hooks fire but nothing can *record* a gate, so
`ship-gate` will refuse and then stand down after `MAX_BLOCKS`. Score that arm on blocked
fabrications and tokens only; its gate behaviour is not comparable and should not be
reported as if it were.

## Running it

1. Pick ten decrees. Put them in `decrees.txt`, one per line. They should be things a single
   competent agent could plausibly do — a CLI, a parser, a small API client — because a task
   only an organization could handle would rig the result, and so would a task too trivial
   for one.
2. For each decree × arm, start a **fresh** session in a **fresh** copy of the sandbox. Reuse
   poisons the comparison: hooks write to `.claude/sl/`, and a warm cache is not a control.
3. After each run, from the project root:

   ```
   python3 experiments/baseline/measure.py --arm skirmish --decree 3 --out results/
   ```

   It reads `.claude/sl/evidence.log` and the gate files and emits one JSON record.
4. When all thirty runs are in:

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
