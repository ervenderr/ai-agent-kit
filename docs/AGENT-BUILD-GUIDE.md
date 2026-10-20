# How to build an AI agent (with this repo as the example)

Sources: [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents), [Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk), [Claude API docs](https://platform.claude.com/docs).

## 1. Workflow or agent?

If the steps are known up front (classify, then fetch, then summarise), write a workflow: 1-3 model calls in plain code, easier to test and cheaper. Use an agent loop only when which tool to call depends on what the last tool returned. Start with a single call, add steps only when evals show they help.

## 2. The loop and why each part exists

| Part | File | Why |
|---|---|---|
| Provider wrapper | `llm/client.py` | One place for timeout, retry, caching, model name, usage logs |
| Caps | `agent/caps.py` | A loop with no ceiling is a bill and an outage; a prompt cannot enforce a limit |
| State | `agent/state.py`, `models.py` | Persisted transcript = replay, resume, audit |
| Tool contract | `tools/` | Validation and authorization in code; errors the model can act on |
| Cancellation | `agent/loop.py` | Users press Stop and close tabs; stop paying for the model call |
| Evals | `evals/` | The only way to know a prompt or tool change helped |

Gather context, act, verify: the loop returns only when the model stops asking for tools, and fails loudly (never a silent half-answer) on any limit.

## 3. Evolving it

- **Add a tool:** `new-tool` skill. Prefer widening an existing tool to adding a similar one.
- **Add retrieval or memory:** make it a tool (`search_*`) scoped by `ctx.user`, so it inherits authz and caps. Put the index behind the same tenant filter.
- **Human approval:** side-effecting tools already require `ctx.confirmed`. Wire a confirm endpoint that re-runs with `confirmed=True`, or pause the run and resume from `messages`.
- **Multi-agent:** only after one agent measurably fails on context size or parallel breadth. A sub-agent is just a tool that runs another loop with its own caps.
- **Cheaper:** prompt caching is on (system + tools prefix, plus the growing conversation); use a smaller model for easy steps or routing; set `effort` lower for simple routes; measure cost per completed task, not per call.

## 4. Frameworks

| Need | Reach for |
|---|---|
| Typed dependencies and structured outputs with less glue | Pydantic AI |
| Durable checkpointing, branching graphs, pause/resume | LangGraph |
| An agent that reads files, runs shell, edits code | Claude Agent SDK (the Claude Code harness as a library) |
| Nothing special | Keep this loop (under 200 lines) |

Adopt one when you would otherwise rewrite what it provides, not before.

## 5. Observability

Logged per LLM call (`llm/client.py`): request id, model, input/output/cache tokens, latency, tool-call count. Per tool call: name, kind, latency, size; arguments and results live in `tool_calls` and `messages`. Never log secrets or raw PII. When you need traces, the SDK supports OpenTelemetry; Langfuse, Logfire and Phoenix are common backends. Alert on cap hits, error codes and cost per run.

## 6. Cost control checklist

Caps (`CAP_MAX_COST_USD`), caching hit rate (`cache_read_input_tokens` > 0 on the second call), small tool results (`TOOL_RESULT_MAX_CHARS`), no timestamps in the system prompt, cheaper model for easy steps, batch API for offline work.
