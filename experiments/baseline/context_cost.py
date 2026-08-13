#!/usr/bin/env python3
"""Measure the static context each baseline arm loads, and print the table.

The cost half of the baseline question needs no runs: it is a property of the
files. It was originally measured by hand, and the figures went into the README
with no method recorded -- so re-measuring later gave 1,587 where the table said
1,488, and there was no way to tell which was wrong without reconstructing the
definition. (Neither was: one counted the `---` delimiters and one did not, at 9
characters across 11 files.) A stated figure whose method is not written down is
exactly what the rest of this repository refuses to accept from an agent, so it
should not be accepted here either.

    python3 experiments/baseline/context_cost.py

What is counted, stated precisely because that is the whole point:

  always-on  the YAML frontmatter of every commands/*.md and agents/*.md, NOT
             counting the `---` delimiter lines. This is what Claude Code reads
             in every session once the plugin is installed, decree or no decree.
             Identical across arms.
  decree     the full text of commands/decree.md, loaded when /sl:decree runs.
  leads      the full text of the agent definitions a muster actually dispatches
             -- two for SKIRMISH, five for FULL.

Characters, not tokens. No Claude tokenizer is available offline, so the token
column is an estimate at CHARS_PER_TOKEN and is labelled as one wherever it is
printed. The character counts are the measurement.

This is a floor, not the cost: it excludes the dispatch conversation, which is
where the real spend is. Nothing here says what the organization catches.

Stdlib only, like everything else here.
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent

# Rough and openly so. Four characters per token is the usual English
# approximation; it is not Claude's tokenizer and is never presented as one.
CHARS_PER_TOKEN = 4

FRONTMATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)

# The leads a muster puts on the field. SKIRMISH fields Development and QC -- the
# truth-audit team, NOT QA, which is a different team with a different gate. Read
# it off decree.md ("under SKIRMISH only DEV-LEAD and QC-LEAD") and off ship-gate's
# required_gates(), which returns ["QC-TRUE"] for a skirmish. Getting this wrong is
# a 469-character error in the skirmish row and nothing else, which is precisely
# the kind of quiet mistake a script fixes and a memory does not.
SKIRMISH_LEADS = ("software-development-lead", "qc-lead")


def read(path):
    return path.read_text(encoding="utf-8", errors="replace")


def frontmatter_chars(path):
    """Characters of YAML frontmatter, excluding the `---` delimiter lines."""
    m = FRONTMATTER.match(read(path))
    return len(m.group(1)) if m else 0


def measure():
    commands = sorted((ROOT / "commands").glob("*.md"))
    agents = sorted((ROOT / "agents").glob("*.md"))
    if not commands or not agents:
        sys.exit(f"no commands/ or agents/ found under {ROOT}")

    always = sum(frontmatter_chars(p) for p in commands + agents)
    decree = len(read(ROOT / "commands" / "decree.md"))

    skirmish_files = [p for p in agents if p.stem in SKIRMISH_LEADS]
    if len(skirmish_files) != len(SKIRMISH_LEADS):
        found = ", ".join(p.stem for p in agents)
        sys.exit(f"expected leads {SKIRMISH_LEADS}, found: {found}")

    return {
        "files": {"commands": len(commands), "agents": len(agents)},
        "always": always,
        "decree": decree,
        "skirmish_leads": sum(len(read(p)) for p in skirmish_files),
        "full_leads": sum(len(read(p)) for p in agents),
    }


def main():
    m = measure()
    arms = [
        ("hooks-only", m["always"], 0, 0),
        ("skirmish", m["always"], m["decree"], m["skirmish_leads"]),
        ("full", m["always"], m["decree"], m["full_leads"]),
    ]

    print(f"Measured from {ROOT.name}: "
          f"{m['files']['commands']} commands, {m['files']['agents']} agents\n")
    head = f"| {'Arm':<11} | {'Always-on':>9} | {'decree.md':>9} | {'Leads':>9} | {'Total':>9} |"
    print(head)
    print("|" + "|".join("-" * len(c) for c in head.split("|")[1:-1]) + "|")
    for name, always, decree, leads in arms:
        total = always + decree + leads
        print(f"| {name:<11} | {always:>9,} | {decree:>9,} | {leads:>9,} | {total:>9,} |")

    print(f"\nAt ~{CHARS_PER_TOKEN} characters per token that is roughly "
          + " / ".join(f"{(a + d + l) // CHARS_PER_TOKEN:,}" for _, a, d, l in arms)
          + " tokens.")
    print("Those three are ESTIMATES -- no Claude tokenizer is reachable here. The "
          "character\ncounts above are what was actually measured.")

    full = sum(arms[2][1:])
    print(f"\nA full muster carries {full / arms[0][1]:.1f}x the static context of the "
          f"control,\nbefore any work happens.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
