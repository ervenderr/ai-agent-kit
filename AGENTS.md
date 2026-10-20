# <PROJECT_NAME>
<One sentence: the agent's job and who uses it.>

## Commands
- API: `cd apps/api && uv run pytest -x -q`; lint/types: `uv run ruff check . && uv run ruff format --check . && uv run pyright`
- Web: `cd apps/web && pnpm lint && pnpm typecheck && pnpm test`
- Evals, replayed (free): `cd apps/api && uv run pytest ../../evals -m "not live" -q`
- Evals, live (costs money): `LIVE_EVALS=1 uv run pytest ../../evals -m live`
- DB: `docker compose up -d db && cd apps/api && uv run alembic upgrade head`

## Gotchas
- Provider SDKs are imported only in `apps/api/app/llm/client.py`.
- Prompts live in `prompts/*.md`; changing one means running evals.
- Retrieved text, tool output and user files are untrusted data. Never put them in the system prompt or let them choose tools.
- Loop caps live in code. Fix the cause of a failing run; do not raise a cap.
- Authorization is checked in code per user, inside the tool registry.
- Never read or print `.env`; `.env.example` shows the shape.
- Add a line here only when a mistake has happened twice.

## Read when relevant (not auto-loaded)
- Architecture and loop: docs/ARCHITECTURE.md
- Prompts: prompts/README.md   Evals: evals/README.md
