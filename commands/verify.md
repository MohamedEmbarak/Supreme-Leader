---
description: Audit every claim in this repository against a real run of the suite.
---

Run the repository-wide claim audit:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/hooks/verify-claims.py"
```

It detects the project's test suite — Python `unittest` or `pytest`, Node via
`npm test`, or Go — runs it once, then checks every stated test figure in every
markdown file against what actually ran. Exit 0 means every claim reproduces.

Report the result plainly. On failures, list each offending file and line, then fix
the figures or mark them `UNVERIFIED`. Do not silence a finding by deleting the claim
unless the claim was genuinely wrong to make.

A file that records measurements from a past run — an audit log, a changelog — may
declare itself historical with an HTML comment reading `truth-lint: historical`, at
the top of the file for the whole file, or at the end of a line for that line alone.
Use it sparingly and only for genuine records: the marker is greppable precisely so
the next auditor can see every exemption at a glance.
