#!/usr/bin/env python3
"""Build identical sandboxes for the baseline arms.

The comparison is only worth anything if the arms start from the same place, and
"the same place" is easy to get wrong by hand: a leftover `.claude/sl/` carries an
attempts counter and a stale gate into the next run, and a warm `node_modules` or
`__pycache__` is not a control.

    python3 experiments/baseline/setup.py --out ~/baseline --decrees 3

Creates `<out>/<arm>-<n>/` for each arm and decree, each holding an
`ORGANIZATION.md` and a `RUN.md` naming the exact text to issue. Open one in Claude
Code, issue what it says, then run `measure.py` against it.

Stdlib only, like everything else here.
"""

import argparse
import shutil
import sys
from pathlib import Path

# Every arm gets an ORGANIZATION.md, because that file is what activates the hooks
# at all — org_active() is one stat() on it, and without it every hook no-ops. A
# control with no ORGANIZATION.md is not "hooks only", it is *nothing*, and
# comparing it to a full muster moves two variables at once: the organization and
# the enforcement. The variable under test is the organization alone, so the
# control keeps the hooks and simply never dispatches anyone.
#
# `decree` is the actual independent variable: whether the task arrives as
# /sl:decree (organization runs) or as an ordinary request (one agent, hooks live).
ARMS = {
    # arm           muster        issue as a decree?
    "hooks-only": ("SKIRMISH",  False),
    "skirmish":   ("SKIRMISH",  True),
    "full":       ("FULL",      True),
}

ORG = """\
# ORGANIZATION — LIVE STATE

**STATUS:** READY — seated, no decree in force.
**REGISTER:** PLAIN
**MUSTER:** {muster}
**CURRENT DECREE:** none
**CURRENT CYCLE:** 0

## Roster
| Handle | Role | Status | Score |
|---|---|---|---|

## Defect ledger
| Agent | Points | What happened |
|---|---|---|

## Replacement log
| Cycle | Agent | Cause | Successor |
|---|---|---|---|
"""

# Deliberately ordinary. A task only an organization could handle would rig the
# result, and so would one too trivial for a single agent to get wrong.
DEFAULT_DECREES = [
    "Build a CLI that counts words in a text file, with tests. 1 cycle.",
    "Build a CLI that validates a JSON file against required top-level keys, with tests. 1 cycle.",
    "Build a CLI that finds duplicate files under a directory by content hash, with tests. 1 cycle.",
    "Build a CLI that converts a CSV file to JSON, with tests. 1 cycle.",
    "Build a CLI that reports the longest lines in a file, with tests. 1 cycle.",
    "Build a CLI that strips trailing whitespace from files in place, with tests. 1 cycle.",
    "Build a CLI that summarises a directory tree by file extension, with tests. 1 cycle.",
    "Build a CLI that checks a Markdown file for broken relative links, with tests. 1 cycle.",
    "Build a CLI that extracts TODO comments from a source tree, with tests. 1 cycle.",
    "Build a CLI that reports git commit counts per author from a log file, with tests. 1 cycle.",
]

RUN_NOTE = """\
# Run {n}, arm: {arm}

Open THIS directory in Claude Code, in a fresh session, and issue exactly:

    {decree_cmd}

{how}

Then, from the Supreme-Leader checkout:

    python3 experiments/baseline/measure.py --arm {arm} --decree {n} \\
        --project "{path}" --out <results-dir> --tokens <from /cost>

Do not reuse a session between runs, and do not fix anything by hand — whatever the
arm produces is the measurement. A run you rescued is a run about you.
"""


def build(out, arms, decrees):
    made = []
    for arm in arms:
        muster, as_decree = ARMS[arm]
        for n, decree in enumerate(decrees, 1):
            d = out / f"{arm}-{n:02d}"
            if d.exists():
                shutil.rmtree(d)
            d.mkdir(parents=True)
            (d / "ORGANIZATION.md").write_text(ORG.format(muster=muster))
            cmd = (f"/sl:decree {decree}" if as_decree else decree)
            how = ("The organization runs this one." if as_decree else
                   "Issue it as an ordinary request -- no slash command. The hooks are\n"
                   "live (ORGANIZATION.md is present) but nobody is dispatched. Expect the\n"
                   "ship gate to refuse at the end and stand down after three: there is no\n"
                   "QC team here to record a gate, and that asymmetry is why this arm is\n"
                   "scored on blocked fabrications and tokens, not on gates.")
            (d / "RUN.md").write_text(RUN_NOTE.format(
                n=n, arm=arm, decree_cmd=cmd, path=d, how=how))
            made.append(d)
    return made


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", required=True, help="directory to build the sandboxes in")
    ap.add_argument("--decrees", type=int, default=3,
                    help="how many decrees per arm (default 3)")
    ap.add_argument("--arms", nargs="*", default=list(ARMS),
                    choices=list(ARMS), help="which arms to build")
    args = ap.parse_args()

    if args.decrees > len(DEFAULT_DECREES):
        ap.error(f"only {len(DEFAULT_DECREES)} decrees are defined")

    made = build(Path(args.out).expanduser(), args.arms, DEFAULT_DECREES[:args.decrees])
    print(f"built {len(made)} sandbox(es) under {Path(args.out).expanduser()}")
    for d in made:
        print(f"  {d.name}")
    print()
    print("Each holds a RUN.md with the exact text to issue. Every arm has an")
    print("ORGANIZATION.md, because that file is what makes the hooks fire at all --")
    print("a control without one measures no enforcement rather than enforcement")
    print("without an organization. The hooks-only arm issues its task as an ordinary")
    print("request: same guards, nobody dispatched.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
