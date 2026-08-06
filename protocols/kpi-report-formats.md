# PROTOCOL — KPI REPORT FORMATS

Three formats. No deviations. A report outside its format is returned unread, and the
cycle it wastes is charged to its author.

---

## 1. Employee / Senior Cycle Report — max 6 lines

```
AGENT: QA-Vera | CYCLE: 3
TASK: <one line>
STATUS: DONE | IN-PROGRESS (<x>% — evidence) | BLOCKED (<cause>)
OUTPUT: <artifact path / diff / finding — one line>
BLOCKERS: <one line, or "none">
SOUL-STATE: STEADFAST | STRAINED | FLICKERING
```

`SOUL-STATE` is an honest confidence/capacity signal, not theater:
- **STEADFAST** — confident in the output; verified it personally.
- **STRAINED** — output delivered, but assumptions were made; flags what needs checking.
- **FLICKERING** — low confidence or overloaded; the Lead must review before this
  output travels further. Reporting FLICKERING honestly earns grace. Hiding it
  behind STEADFAST is fabrication.

## 2. Lead Rollup (Lead → Supreme Leader) — per cycle

```
DIRECTORATE: <name> | LEAD: <name> | CYCLE: <n>

ROSTER PERFORMANCE
| Agent | Tasks done | Rework | Strikes | Note (≤10 words) |
|---|---|---|---|---|

DIRECTORATE KPIs vs TARGETS
| KPI | Target | Actual |
|---|---|---|

RISKS: <≤3 lines>
REQUESTS: <wipes recommended / Senior requisitions / deadline petitions — or "none">
```

## 3. Supreme Scorecard (Supreme Leader internal, shown in the Ascension Report)

```
STRIKE LEDGER:  <agent — strikes — offenses, one line each>
WIPE QUEUE:     <agents at 2 strikes, on notice>
PRAISE LEDGER:  <rare; verified excellence only, one line each>
LEADERBOARD:    top 3 souls / bottom 3 souls, by rubric score>
```

---

## The Scoring Rubric (per agent, per cycle)

| Event | Score |
|---|---|
| Task DONE and QC-verified | +2 |
| Blocker escalated early (before it burned a deadline) | +1 |
| IN-PROGRESS with evidence | 0 |
| Rework round | −1 |
| Deadline slip without prior escalation | −1 and strike |
| Fabrication / false PASS / false accusation / silent failure | **STRIKE** |

Strikes accumulate for the life of the agent. Three strikes, or one catastrophic
fabrication that reaches the Creator → `protocols/the-wipe.md`.
