#!/usr/bin/env python3
"""Measure one run of the baseline experiment, or report across all of them.

Reads only what the run actually left behind — the evidence ledger and the gate
files. Nothing here estimates, infers, or reconstructs: a quantity this script
cannot observe is emitted as null rather than as a guess, because the entire
point of the experiment is to replace an assumption with a measurement.

    python3 experiments/baseline/measure.py --arm skirmish --decree 3 \\
        --out experiments/baseline/results/ --tokens 41200
    python3 experiments/baseline/measure.py --report experiments/baseline/results/

Stdlib only, like the hooks.
"""

import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path

ARMS = ("hooks-only", "skirmish", "full")

# The refusal headers the hooks emit. Matched in both registers, since a run may
# have been done with the lore overlay on and the count must not depend on that.
REFUSALS = {
    "unverified-test-claim": re.compile(r"UNVERIFIED TEST CLAIM BLOCKED"),
    "fabricated-import": re.compile(r"FABRICATED IMPORT BLOCKED"),
    "fabricated-package": re.compile(r"FABRICATED PACKAGE BLOCKED"),
    "ship-gate-refused": re.compile(r"SHIP GATE — REFUSED"),
    "qa-pass-denied": re.compile(r"QA PASS DENIED"),
}


def read_ledger(root):
    p = root / ".claude" / "sl" / "evidence.log"
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except Exception:
                continue
    return out


def read_gates(root):
    d = root / ".claude" / "sl"
    gates = {}
    if not d.is_dir():
        return gates
    for f in sorted(d.glob("gate-*.json")):
        try:
            gates[f.stem[5:]] = json.loads(f.read_text())
        except Exception:
            gates[f.stem[5:]] = None
    return gates


def measure(root, arm, decree, tokens, seconds):
    ledger = read_ledger(root)
    cmds = [r for r in ledger if r.get("type") == "cmd"]
    results = [r for r in ledger if r.get("type") == "result"]
    gates = read_gates(root)

    # Refusals are counted from recorded output. A hook's own stderr does not pass
    # through the ledger, so this undercounts unless the operator pasted refusals
    # back — which is why `refusals_source` is stated rather than left implied.
    blob = "\n".join(r.get("tail", "") for r in results)
    refusals = {k: len(rx.findall(blob)) for k, rx in REFUSALS.items()}

    qa = gates.get("QA-PASS") or {}
    return {
        "arm": arm,
        "decree": decree,
        "recorded_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "commands": len(cmds),
        "results_recorded": len(results),
        "refusals": refusals,
        "refusals_total": sum(refusals.values()),
        "refusals_source": "evidence-ledger result tails only",
        "gates_recorded": sorted(gates),
        "qa_pass_hook_written": bool(qa) and "hook-verified" in (qa.get("note") or ""),
        "tokens": tokens,
        "seconds": seconds,
    }


def report(results_dir, declared=None, allow_partial=False):
    """Summarise the matrix — and withhold the comparison unless it is complete.

    This used to print the warning *and* the table, which is a warning in the same
    sense that a sign is a lock. The README claimed it "refuses to report on a
    partial matrix"; it did not, and the gap between those two was found by reading
    the code to check the sentence rather than by trusting it. A means table is the
    thing that gets screenshotted, so withholding it is the only version of this
    guard that does anything.

    The intended matrix defaults to the arms that actually have runs, because the
    experiment is designed to be scoped down: the README recommends two arms of the
    three, and a fixed check against ARMS would call a finished two-arm run partial
    forever, which trains the reader to ignore it. Pass --arms to hold the run to a
    matrix it has not filled yet.
    """
    records = []
    for f in sorted(Path(results_dir).glob("*.json")):
        try:
            records.append(json.loads(f.read_text()))
        except Exception:
            print(f"  skipped unreadable {f.name}", file=sys.stderr)
    if not records:
        print("No results yet. Nothing to report.")
        return 1

    by_arm = {a: [r for r in records if r.get("arm") == a] for a in ARMS}
    present = [a for a in ARMS if by_arm[a]]
    intended = list(declared) if declared else present

    # A matrix is complete when there is something to compare and the arms are
    # balanced. Unequal n is not a comparison either — three of one arm against one
    # of another is an anecdote with a mean printed on it.
    counts = {a: len(by_arm[a]) for a in intended}
    empty = [a for a in intended if not counts[a]]
    unbalanced = len(set(counts.values())) > 1
    complete = len(intended) >= 2 and not empty and not unbalanced

    print(f"{len(records)} run(s) across {len(present)} arm(s)\n")

    if not complete and not allow_partial:
        for a in intended:
            print(f"  {a:<12} {counts[a]} run(s)")
        why = []
        if len(intended) < 2:
            why.append("a comparison needs at least two arms")
        if empty:
            why.append(f"no runs for: {', '.join(empty)}")
        if unbalanced and not empty:  # with an empty arm this is implied, not news
            why.append("the arms have unequal run counts "
                       + "(" + ", ".join(f"{a}={counts[a]}" for a in intended) + ")")
        print(f"\nNo comparison printed: {'; '.join(why)}.")
        print("A means table from a partial matrix is the thing that ends up quoted, "
              "so it is withheld rather than captioned. Finish the runs, or pass "
              "--partial to see it anyway and not publish it.")
        return 1

    header = f"{'arm':<12}{'n':>3}{'refusals':>10}{'commands':>10}{'tokens':>10}"
    print(header)
    print("-" * len(header))
    for arm in intended:
        rows = by_arm[arm]
        if not rows:
            print(f"{arm:<12}{0:>3}{'-':>10}{'-':>10}{'-':>10}")
            continue
        tok = [r["tokens"] for r in rows if r.get("tokens")]
        print(f"{arm:<12}{len(rows):>3}"
              f"{statistics.mean(r['refusals_total'] for r in rows):>10.1f}"
              f"{statistics.mean(r['commands'] for r in rows):>10.1f}"
              f"{(f'{statistics.mean(tok):.0f}' if tok else '-'):>10}")

    if not complete:
        print("\nPARTIAL MATRIX -- shown because --partial was passed. Not a result.")

    missing = [r for r in records if not r.get("tokens")]
    if missing:
        print(f"\n{len(missing)} run(s) have no token count. The cost side of the "
              f"question is unanswered until they do -- read /cost and re-record with "
              f"--tokens.")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--arm", choices=ARMS)
    ap.add_argument("--decree", type=int)
    ap.add_argument("--project", default=".", help="project root of the finished run")
    ap.add_argument("--out", help="directory to write the record into")
    ap.add_argument("--tokens", type=int, help="from /cost — the harness cannot see it")
    ap.add_argument("--seconds", type=float, help="wall clock for the run")
    ap.add_argument("--report", help="summarise a results directory instead")
    ap.add_argument("--arms", nargs="*", choices=ARMS,
                    help="with --report: the intended matrix (default: the arms "
                         "that have runs)")
    ap.add_argument("--partial", action="store_true",
                    help="with --report: print the comparison from an incomplete "
                         "matrix anyway. It is not a result.")
    args = ap.parse_args()

    if args.report:
        return report(args.report, args.arms, args.partial)
    if not (args.arm and args.decree is not None and args.out):
        ap.error("--arm, --decree and --out are required unless --report is given")

    rec = measure(Path(args.project), args.arm, args.decree, args.tokens, args.seconds)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    dest = out / f"{args.arm}-{args.decree:02d}.json"
    dest.write_text(json.dumps(rec, indent=2) + "\n")
    print(f"wrote {dest}")
    if rec["tokens"] is None:
        print("  no --tokens given; this run's cost is unmeasured")
    return 0


if __name__ == "__main__":
    sys.exit(main())
