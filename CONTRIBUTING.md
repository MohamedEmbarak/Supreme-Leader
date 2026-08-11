# Contributing

This repo is prompts, markdown, and a small enforcement layer of Python-stdlib hooks.
There is nothing to build; hook changes must ship with their test commands actually run
(feed each hook a payload on stdin and check the exit code — see the hooks' docstrings).

## The one rule

**Every claim in this repository must be true of the files in this repository.**

If the README says the Leads carry `model:` frontmatter, open one and check. If a protocol
references `templates/senior-contract.md`, that file must exist at that path. A repo whose
whole premise is that fabrication gets you erased cannot itself ship claims it does not
support — and the first person to notice will say so publicly.

Before opening a PR, confirm:

- Every file path mentioned in prose actually exists.
- Every rule you added is consistent with `DOCTRINE.md`, and does not contradict a rule in
  another agent or protocol file.
- Any command in the README runs as written.
- You have not added a benchmark, a metric, or a result that was not measured.

## What is welcome

- **New directorates or Leads**, in the same frontmatter format as `agents/*.md`, with a KPI
  table and a stated failure mode.
- **Runtime ports** — CrewAI, AutoGen, LangGraph, OpenAI Agents SDK. Say plainly which parts
  survived the port and which did not. A port that drops the QC layer is a different system
  and should say so.
- **Run reports**, via the "Submit a decree" issue template. Reports where the organization
  broke character, or where a fabrication slipped past QC, are worth more than successes.
- **Doctrine defects** — two rules that cannot both be obeyed.

## What is not

- Benchmarks or accuracy claims without a reproducible method. There are none in this repo
  today, deliberately, and adding unsupported ones is the one change that will always be
  rejected.
- More lore for its own sake. Every piece of theatre here maps to a mechanism. If a new rule
  does not change what an agent actually does, it is decoration.
- Verbosity. The Law of Silence applies to contributors too.

## Style

Markdown, wrapped near 95 characters, no trailing whitespace. Keep agent files terse — they
are prompts, and every line you add is a line the model pays for on every single run.
