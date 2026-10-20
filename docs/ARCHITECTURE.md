# Architecture

One FastAPI service runs a bounded tool loop over Postgres; a thin Next.js page streams it.

```
 browser (apps/web)                      apps/api
 ┌──────────────┐  POST /runs (SSE)  ┌─────────────────────────────────────────┐
 │ chat page    │ ─────────────────▶ │ routes/runs.py   auth -> RunState       │
 │ tool cards   │ ◀── events ─────── │      │                                  │
 │ Stop button  │  POST /cancel ───▶ │      ▼                                  │
 └──────────────┘                    │ agent/loop.py    caps ─▶ LLM ─▶ tools   │
                                     │      │            ▲        │      │     │
                                     │      │       llm/client.py │  tools/registry.py
                                     │      │       (only SDK use)│  authz ▸ validate ▸ run ▸ truncate
                                     │      ▼                     ▼            │
                                     │ Postgres: runs, messages, tool_calls, notes, users
                                     └─────────────────────────────────────────┘
```

## The loop (`agent/loop.py`)

Each iteration: check caps and cancellation, call the LLM (streaming), and if it asked for no tools return the answer. Otherwise run the requested tools (independent calls in parallel with `asyncio.gather`), append the results as one user message, persist, repeat.

- **Events** (`text_delta`, `tool_call`, `tool_result`, `final`, `error`) are yielded by an async generator; the route frames them as SSE `data:` lines. The first event is `run` with the run id.
- **Every run ends with `final` or `error`.** Caps, truncation (`max_tokens`), refusals, repeated bad tool args and final tool errors all produce an `error` with a stable `code`.
- **Cancellation.** `POST /runs/{id}/cancel` sets an event on the in-process `RunState`; `_until_cancelled` stops waiting on the LLM stream and closes it. A client disconnect cancels the task, which closes the same stream (`aclosing` in the route). Both end with status `cancelled`.
- **A step that asks for tools with no step left to read the results is refused** (`cap_exceeded:steps`) rather than run.

## Tools (`tools/`)

`Tool` = name, description, Pydantic args model (JSON schema generated from it, `extra="forbid"`), `scope`, `side_effect`, `run(args, ctx)`. `Registry.execute` never raises. In order: unknown tool, scope check against `ctx.user.scopes` (permission error, `final`), confirmation for side effects (`ctx.confirmed`, `final`), Pydantic validation (short actionable error), run, truncate. Final errors end the run (`tool_denied`, `confirmation_required`).

## Data model

`users(id, email, api_token, scopes)`, `notes(user_id, title, body)`, `runs(id, user_id, status, input, final_output, cost, steps, created_at)`, `messages(run_id, idx, role, content JSON)`, `tool_calls(run_id, idx, name, args, result_size, latency_ms, error)`. `messages` holds the provider-format transcript including thinking blocks, so a run can be replayed (`GET /runs/{id}`) or resumed by loading it back into `RunState.messages`. Every query filters by the authenticated user.

## Failure modes

| Failure | Behaviour |
|---|---|
| Cap hit (steps, tool calls, seconds, input tokens, cost) | `error` `cap_exceeded:<kind>`, run `failed` |
| Model truncated or refused | `error` `max_tokens` / `refusal` |
| Bad tool args twice | `error` `invalid_tool_args` (one repair allowed) |
| Permission denied / unconfirmed side effect | run stops, `tool_denied` / `confirmation_required` |
| Provider 429/5xx | SDK retries with backoff (`LLM_MAX_RETRIES`), then `internal` |
| Client disconnect or Stop | LLM stream closed, status `cancelled` |
| Process restart mid-run | run stays `running` in the DB; reconcile on startup if that matters |

## Known limits (deliberate)

`ACTIVE` runs and the per-user concurrency limit live in process memory (one worker). Auth is a placeholder bearer token. `search_notes` has no GIN index. No per-user request rate limit beyond concurrency.
