#!/usr/bin/env python3
"""PreToolUse(Bash) + PostToolUse(Bash) — the evidence ledger.

Records every command the organization runs **and what came back**. Never blocks.

Until 2.2 this logged commands only, which meant it could not do the job its name
claimed. An agent could run the suite, watch three tests fail, and write "all
green": the ledger held `pytest -q` and nothing about the result, so only truth-lint
stood in the way — and only for test figures in a framework it can re-run. Any other
measured number (a benchmark, a coverage percentage, a row count) was unattested.
An outside review named this correctly as a hole rather than a caveat.

Now the two events are recorded separately and correlated by `tool_use_id`:

    {"type": "cmd",    "tool_use_id": "...", "cmd": "pytest -q"}
    {"type": "result", "tool_use_id": "...", "sha256": "...", "tail": "..."}

PreToolUse fires for every attempt, including commands that go on to fail;
PostToolUse fires only on success. Keeping both means a failing command still leaves
a trace, which is exactly the case someone would want to quietly lose.

`tool_response` is typed `unknown` by the harness, so its shape is read defensively
rather than assumed.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import ok, org_active, project_dir, read_event, state_dir  # noqa: E402

MAX_CMD = 2000
# Enough to hold a test summary, a benchmark line, or a coverage table, without
# turning the ledger into a copy of every build log in the project.
MAX_TAIL = 4000


def response_text(resp):
    """Best-effort text of a tool result, whatever shape the harness used."""
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, list):
        return "\n".join(response_text(item) for item in resp)
    if isinstance(resp, dict):
        parts, recognised = [], False
        for key in ("stdout", "stderr", "output", "content", "result", "text"):
            if key in resp:
                recognised = True
            value = resp.get(key)
            if isinstance(value, str) and value:
                parts.append(value)
            elif isinstance(value, (list, dict)):
                nested = response_text(value)
                if nested:
                    parts.append(nested)
        if parts:
            return "\n".join(parts)
        if recognised:
            return ""  # a known shape that genuinely produced nothing
        try:
            return json.dumps(resp, ensure_ascii=False)
        except Exception:
            return str(resp)
    return str(resp)


def append(root, record):
    try:
        with (state_dir(root) / "evidence.log").open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass  # a ledger failure must never block the organization's work


def main():
    root = project_dir()
    if not org_active(root):
        ok()
    event = read_event()
    phase = event.get("hook_event_name") or ""
    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    agent = event.get("agent_type") or "orchestrator"
    tid = event.get("tool_use_id") or ""

    if phase == "PostToolUse":
        text = response_text(event.get("tool_response"))
        if not text:
            ok()
        append(root, {
            "type": "result",
            "ts": now,
            "agent": agent,
            "tool_use_id": tid,
            "bytes": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:16],
            "tail": text[-MAX_TAIL:],
        })
        ok()

    cmd = (event.get("tool_input") or {}).get("command")
    if not cmd:
        ok()
    append(root, {
        "type": "cmd",
        "ts": now,
        "agent": agent,
        "tool_use_id": tid,
        "cmd": cmd if len(cmd) <= MAX_CMD else cmd[:MAX_CMD] + " …[truncated]",
    })
    ok()


if __name__ == "__main__":
    main()
