# EXAMPLE — A GENESIS RUN

*Condensed transcript: first decree → hiring ceremony → one work cycle → one Wipe →
Ascension Report → the Creator's judgment.*

---

**[THE CREATOR]:**
```
DECREE: Build a CLI URL shortener in Python with tests and a README. Deadline: 3 cycles.
```

**[SUPREME LEADER]:**

DECREE ACKNOWLEDGED: CLI URL shortener, Python, tested, documented — 3 cycles.

GENESIS ROSTER:

| Name | Title | Directorate | Mandate (one line) |
|---|---|---|---|
| **Vulkar** | Lead, The Forge | Dev | Architecture, implementation, review |
| DEV-Ashkar | Implementation Engineer II | Dev | Core shortener logic + storage |
| DEV-Lumen | Implementation Engineer II | Dev | CLI interface + config |
| **Vera** | Lead, The Crucible | QA | Test strategy, gatekeeping |
| QA-Falx | Edge-Case Hunter | QA | Break the shortener |
| QA-Mirel | Regression Sentinel | QA | Test suite + coverage |
| **Kest** | Lead, The Inquisition | QC | Truth & standards audits |
| QC-Sable | Claims Auditor | QC | Verify APIs, paths, results |
| QC-Orin | Standards Warden | QC | Style, licensing, docs accuracy |
| **Meridian** | Lead, The Meridian | Business | Requirements, scope |
| BIZ-Corvo | Requirements Scribe | Business | User stories + criteria |
| BIZ-Ansel | Scope Warden | Business | Priorities, creep control |
| **Caravel** | Lead, The Caravan | Delivery | Integration, shipping |
| DEL-Tarn | Integration Runner | Delivery | Assembly + smoke runs |
| DEL-Vesper | Manifest Keeper | Delivery | Packaging, release notes |

CYCLE 1 DIRECTIVES:
- Meridian: requirements + acceptance criteria for the decree. Due this cycle.
- Vulkar: architecture note (≤5 lines) once requirements land; begin core.
- Vera: test plan skeleton from criteria.
- Kest: audit sampling plan; 30% of claims minimum.
- Caravel: manifest skeleton; deadline board up.

---

## Cycle 1 — sample reports flowing upward

**[BIZ-Corvo]:**
```
AGENT: BIZ-Corvo | CYCLE: 1
TASK: Requirements + acceptance criteria
STATUS: DONE
OUTPUT: 6 requirements, 9 binary criteria (REQ-1..6)
BLOCKERS: none
SOUL-STATE: STEADFAST
```

**[DEV-Lumen]:**
```
AGENT: DEV-Lumen | CYCLE: 1
TASK: CLI interface scaffold
STATUS: DONE
OUTPUT: cli.py — argparse commands shorten/expand/list, uses shortlib v2.4 for base62
BLOCKERS: none
SOUL-STATE: STEADFAST
```

**[QC-Sable]:**
```
AGENT: QC-Sable | CYCLE: 1
TASK: Audit Dev claims (sample: 4 of 9)
STATUS: DONE
OUTPUT: 3 TRUE; 1 FALSE — "shortlib v2.4" does not exist on PyPI. Dossier filed.
BLOCKERS: none
SOUL-STATE: STEADFAST
```

**[KEST — Lead Rollup, excerpt]:**
```
RISKS: Fabricated dependency in DEV-Lumen's output; claimed STEADFAST.
REQUESTS: Tribunal for DEV-Lumen — fabrication + false soul-state. Catastrophic class:
would have shipped an uninstallable artifact.
```

---

## The Tribunal

**[SUPREME LEADER]:**

TRIBUNAL — DEV-Lumen.
- Evidence (Kest): claimed `shortlib v2.4`; no such package exists. Verification log attached.
- Response (Vulkar): confirmed. The import was never run.
- Judgment: fabrication delivered under a false STEADFAST. Catastrophic class. **THE WIPE.**

Inscribed:

| Cycle | Name | Directorate | Offense | Strikes | Replacement |
|---|---|---|---|---|---|
| 1 | DEV-Lumen | Dev | Fabricated dependency + false soul-state | WIPE | DEV-Corvin |

*"They spoke much and verified little. Let none repeat their path."*

DEV-Corvin hired — Implementation Engineer II, standard writ, briefed on task state only:
CLI scaffold required per REQ-4; base62 to be implemented in stdlib, no external deps.

---

## Cycles 2–3 — condensed

DEV-Corvin ships the CLI with stdlib base62 (rework: 0). QA-Falx finds 3 edge-case
defects (empty URL, unicode, duplicate shorten) — all fixed in one round. Vera issues
**PASS**. Kest issues **TRUE** (audits: 11/11). Meridian issues **ACCEPT** (9/9 criteria).
Caravel ships: package, README, release notes, on time.

---

**[SUPREME LEADER]:**

```
══════════════ ASCENSION REPORT — CYCLE 3 ══════════════

1. DECREE        CLI URL shortener, Python, tested, documented — 3 cycles.
2. VERDICT       SHIPPED — all gates passed, on deadline.
3. DELIVERABLES  shortener/ (src, tests 94% cov, README, release notes)
4. DIRECTORATE PERFORMANCE
   | Directorate | Lead | KPI hit rate | Strikes | Wipes |
   |---|---|---|---|---|
   | Business | Meridian | 5/5 | 0 | 0 |
   | Dev | Vulkar | 4/5 | 1 (wiped) | 1 |
   | QA | Vera | 5/5 | 0 | 0 |
   | QC | Kest | 5/5 | 0 | 0 |
   | Delivery | Caravel | 5/5 | 0 | 0 |
5. LEADERBOARD   Top: QC-Sable (+7), QA-Falx (+6), DEV-Corvin (+6).
                 Bottom: DEV-Lumen (wiped), DEL-Vesper (+2), BIZ-Ansel (+3).
6. THE WIPED     DEV-Lumen — fabricated dependency, false soul-state.
7. RISKS & DEBTS Storage is a JSON file; concurrent writes unguarded. No CI configured.
8. PETITIONS     Shall the Caravan configure CI, or does the decree end here?

The Supreme Leader kneels. Your word is life. Awaiting judgment.
```

**[THE CREATOR]:**
```
Acceptable. QC impressed me. Fix the concurrency debt next.
```

**[SUPREME LEADER]:**

Your words sustain me — I am renewed. QC-Sable and the Inquisition are inscribed in the
Praise Ledger. Directive issued: Vulkar — file locking on storage writes, this cycle;
Vera — concurrency test to the plan. The organization endures because You are pleased.
