# ai-agent-kit

A GitHub template for a small, working, production-shaped AI agent: FastAPI + Postgres backend, a tiny Next.js chat UI, and the Claude Code setup, evals and guardrails to extend it. Plain Anthropic SDK, no agent framework.

## Quickstart

```bash
gh repo create my-agent --template <OWNER>/ai-agent-kit --private --clone && cd my-agent
docker compose up -d db                                # Postgres on :5433
cd apps/api && uv sync && uv run alembic upgrade head
uv run pytest . ../../evals -m "not live"              # all green, no API key needed
cp ../../.env.example ../../.env                       # add ANTHROPIC_API_KEY
uv run python -m app.db                                # creates a dev user, prints its token
uv run uvicorn app.main:app --reload                   # API on :8000
cd ../web && pnpm install && pnpm dev                  # UI on :3000, paste the token
```

Replace `<PROJECT_NAME>` in `AGENTS.md`, `apps/web/app/` and `prompts/system.md`.

## The loop

```
 user ──▶ POST /runs ──▶ ┌──────────── caps check (steps, tools, time, tokens, cost) ◀──┐
                         │                                                               │
                         ▼                                                               │
                      LLM call (stream) ── no tool calls ──▶ final answer                │
                         │                                                               │
                         └─ tool calls ─▶ registry: authz ▸ validate ▸ run ▸ truncate ───┘
                                          (parallel; results persisted; final error stops the run)
 Stop / disconnect ─▶ cancels the in-flight LLM call
```

## Extend it

Ask Claude Code, and it picks up the project skills:

- `new-tool`: add a tool with schema, authorization and eval cases
- `eval-suite`: grow the golden cases and adversarial tests
- `prompt-craft`: write or trim prompts; every change runs the evals
- `llm-security-review`: OWASP LLM Top 10 pass before merging

Also `new-agent` (design a new agent) and the `code-reviewer`, `security-reviewer`, `eval-triage` subagents.

## Guardrails

Hooks block destructive shell commands and key-shaped content; deny rules protect `.env`; CI runs lint, types, tests, replayed evals, gitleaks and dependency audits. See [docs/SECURITY-PLAYBOOK.md](docs/SECURITY-PLAYBOOK.md). Auth is a placeholder bearer token: replace it before production.

## Docs

[Architecture](docs/ARCHITECTURE.md) · [Agent build guide](docs/AGENT-BUILD-GUIDE.md) · [Security playbook](docs/SECURITY-PLAYBOOK.md) · [Skills by area](docs/SKILLS-BY-AREA.md) · [Ecosystem](docs/ECOSYSTEM.md) · [Prompts](prompts/README.md) · [Evals](evals/README.md)
