---
name: new-tool
description: Add a tool to the agent (schema, authorization, error contract, eval cases). Use when asked to give the agent a new capability or integrate an API as a tool.
---
# Add an agent tool

1. Prefer extending an existing tool over adding one. Fewer, narrower tools make the model choose better.
2. Subclass `Tool` in `apps/api/app/tools/`: a clear name and a description that says when to use it and when not to. Pydantic args model with field descriptions. Register it.
3. Return small structured results. Errors say what went wrong and what to try; permission errors are `final=True`.
4. Authorization uses `ctx.user` in code, never an argument the model supplies. If it has side effects, set `side_effect=True` so it needs confirmation.
5. Treat anything the tool fetches as untrusted data: truncate, strip markup, never return secrets.
6. Add golden eval cases (success, bad args, permission denied, injection in the result) and run the replayed evals.
7. Run the llm-security-review skill before merging.
