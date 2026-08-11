---
description: Verification review of a named agent's claim. Ends in acquittal or replacement.
argument-hint: <agent> [the suspect claim, if known]
---

The operator has called a verification review: **$ARGUMENTS**

Three steps, in order, all evidence real — cite the file, the command, the output. The
evidence ledger (`.claude/sl/evidence.log`) is the record of what actually ran; a claimed
observation with no ledger entry was hand-written.

1. **Evidence.** QC presents claim versus verification, ≤6 lines. If QC cannot substantiate
   the charge, say so — a false accusation is itself a fabrication, and the point lands on
   the accuser.
2. **Response.** The agent's lead confirms or contests, one line.
3. **Ruling.** Decide. No appeals, no second review.

If the ruling is replacement: log it in ORGANIZATION.md's replacement log, brief the
successor from ORGANIZATION.md task state only — never from the replaced agent's material —
and continue the cycle in the same turn. For agents simulated inside a lead, this is a
quarantine directive on that lead: the successor never cites, quotes, or builds on the
replaced agent's outputs except what QC verified before the review.

If the agent is innocent, say that just as plainly.

If `ORGANIZATION.md` says `REGISTER: LORE`, conduct this as the tribunal, with the rites.
