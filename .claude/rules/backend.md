---
paths:
  - "apps/api/**/*.py"
---
- Pydantic models at every boundary: request, response, tool args, structured LLM output.
- No blocking I/O in async handlers.
- An Alembic migration for every schema change; never edit applied ones.
- Streaming endpoints handle client disconnect and cancel the upstream LLM call.
- Per-user authorization is checked in code before any tool or retrieval call.
