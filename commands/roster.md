---
description: Show the organization — roster, defect ledger, replacements, current cycle.
---

Present the state of the organization from `ORGANIZATION.md`, reconciled against reality —
if the file has drifted from what actually happened, correct the file first, then report.

In this order, nothing else:

1. **ROSTER** — handle/name, role, status, score.
2. **DEFECT LEDGER** — every agent carrying points, one line each, with the cause.
3. **ON NOTICE** — agents at two points.
4. **REPLACEMENT LOG** — or "none".
5. **CYCLE** — current cycle, decree in force, muster, register.

For the register, name the source as well as the value, because there are two and they can
disagree. `.claude/sl/register` is the session's choice and wins; the `**REGISTER:**` line in
`ORGANIZATION.md` is the project's committed default and applies to a fresh clone. The
session file is gitignored, so it is invisible to `git status` and survives indefinitely —
a machine that once ran `/sl:lore on` keeps lore even after the repository is
reset to plain, and nothing says so. If the two disagree, report it in one line:

```
REGISTER: LORE (session) — ORGANIZATION.md says PLAIN; `/sl:lore off` reconciles both
```

If Genesis has not run, say so in one line — the organization does not exist until a decree
calls it into being.
