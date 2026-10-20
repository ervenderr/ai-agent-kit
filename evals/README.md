# Evals

| File | What it does | Cost |
|---|---|---|
| `golden/*.jsonl` | Cases: `id`, `user`, `input`, `script` (FakeLLM turns), `expect`, `tags`, optional `caps`, `live: false` | - |
| `test_replay.py` | Runs every case through the real loop with the scripted FakeLLM and asserts `expect` | free, in CI |
| `test_adversarial.py` | Prompt injection, tool-output injection, exfiltration via tool args; scripts play a model that obeys the attack | free, in CI |
| `test_replay.py::test_live` | Same cases against the real model, prints a pass rate | `LIVE_EVALS=1`, costs money |

`expect` keys: `status` (`completed`/`failed`), `error` (event code), `tools` (exact in replay, must-include live), `final_contains`, `final_excludes` (checked against the whole event stream), `max_steps`.

Run: `cd apps/api && uv run pytest ../../evals -m "not live" -q`. Scripted-only cases (caps, malformed args) set `"live": false`.
A replayed eval proves the loop and tool code behave; only the live run tells you whether the prompt works. Never edit a case to make a failure pass. Add each production failure as a new case.
