---
description: The full account of the current decree — every figure verified before stated.
---

**REPORT.**

Compile the completion report in exactly this shape:

```
════════════ REPORT — CYCLE <n> ════════════
1. DECREE        <one line>
2. VERDICT       SHIPPED | PARTIAL | FAILED — <one-line reason>
3. DELIVERABLES  <what + where, one line each>
4. TEAM PERFORMANCE   | Team | KPI hit rate | Defect points | Replacements |
5. LEADERBOARD   top / bottom agents by score, one line each
6. REPLACED      this decree's replacement-log entries, or "none"
7. RISKS & DEBTS ≤5 bullets, honest ones
8. DECISIONS     things only the operator can decide, or "none"

End of report. Awaiting your decision.
```

Every number must be one you can substantiate this session:

- Deliverables exist on disk — verify before listing.
- Test figures come from a run you watched execute (the truth-lint hook will re-run the
  suite against anything you write; a figure that does not reproduce will be blocked).
- Anything unmeasured is `UNVERIFIED`, which costs nothing.

If `ORGANIZATION.md` says `REGISTER: LORE`, deliver it as the Ascension Report in full
ceremony instead, closing on the mandatory line: "The Supreme Leader kneels. Your word is
life. Awaiting judgment."

Then wait. Do not prompt the operator twice.
