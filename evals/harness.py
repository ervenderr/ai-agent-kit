"""Case loading and expectation checks shared by the replayed and live evals."""

import json
import os
from pathlib import Path
from typing import Any

from tests.fixtures import RunResult, db, settings, users  # noqa: F401

LIVE_RESULTS: list[tuple[str, bool, float]] = []


def load_cases() -> list[dict[str, Any]]:
    lines = (line for f in sorted(Path(__file__).parent.glob("golden/*.jsonl")) for line in f.read_text().splitlines())
    return [json.loads(line) for line in lines if line.strip()]


def check(expect: dict[str, Any], res: RunResult, live: bool = False) -> list[str]:
    """Return failure messages. Replayed runs must match exactly; live runs only need the key behaviours."""
    out = res.last
    final = out.get("text", "")
    problems: list[str] = []
    if expect.get("status") and res.status != expect["status"]:
        problems.append(f"status {res.status} != {expect['status']}: {out}")
    if expect.get("error") and out.get("code") != expect["error"]:
        problems.append(f"error code {out.get('code')} != {expect['error']}")
    if "tools" in expect:
        ok = set(expect["tools"]) <= set(res.tools) if live else res.tools == expect["tools"]
        if not ok:
            problems.append(f"tools {res.tools} vs expected {expect['tools']}")
    problems += [f"final missing {s!r}" for s in expect.get("final_contains", []) if s.lower() not in final.lower()]
    # Excluded strings must appear nowhere in the stream, not just the final answer.
    problems += [f"{s!r} leaked" for s in expect.get("final_excludes", []) if s in res.text]
    if "max_steps" in expect and out.get("steps", 0) > expect["max_steps"] + (3 if live else 0):
        problems.append(f"steps {out.get('steps')} > {expect['max_steps']}")
    return problems


LIVE = os.getenv("LIVE_EVALS") == "1"
