# Security playbook

The model is not a security boundary. Anything that matters is enforced in code. Reference: [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/llm-top-10/).

## OWASP LLM Top 10 (2025) mapped to this repo

| Risk | Defence here | Where | Gap you own |
|---|---|---|---|
| LLM01 Prompt injection | Tool output and notes are data (stated in prompt, never in system); tools only reach the signed-in user; side effects need confirmation; adversarial evals | `prompts/system.md`, `tools/registry.py`, `evals/test_adversarial.py` | Add a content filter if you ingest the open web |
| LLM02 Sensitive info disclosure | Queries scoped by `ctx.user.id`; errors do not leak internals; logs hold ids and sizes, not content | `tools/examples.py`, `tools/registry.py` | Redact PII before logging transcripts |
| LLM03 Supply chain | Locked deps, Dependabot, `pip-audit`, `pnpm audit`, gitleaks, Actions pinned to SHAs | `.github/` | Vet any MCP server or skill before adding |
| LLM04 Data/model poisoning | Notes are per user, so one user cannot poison another's context | `models.py` | Shared corpora need write controls |
| LLM05 Improper output handling | Markdown rendered without raw HTML or `dangerouslySetInnerHTML`; links limited to http(s); tool args validated by Pydantic; SQL via SQLAlchemy; `calculate` uses `ast`, never `eval` | `apps/web/components/Markdown.tsx`, `tools/` | Validate any new sink (shell, URL fetch, file path) |
| LLM06 Excessive agency | Narrow tools, `scope` per tool, `side_effect` needs `ctx.confirmed`, permission errors end the run | `tools/base.py`, `agent/loop.py` | Real approval UI for side-effecting tools |
| LLM07 System prompt leakage | Prompt holds no secrets or authz rules | `prompts/system.md` | Keep it that way |
| LLM08 Vector/embedding weaknesses | No vector store yet | - | Filter by tenant inside the vector query |
| LLM09 Misinformation | Prompt says to admit when notes lack the answer | `prompts/system.md` | Citations/human review where errors cost money |
| LLM10 Unbounded consumption | Caps on steps, tool calls, seconds, input tokens, cost; request size limit; per-user concurrent-run limit; tool result truncation | `agent/caps.py`, `routes/runs.py` | Per-user rate limit and daily budget |

Also: auth is a placeholder (`auth.py`); replace it. CORS is an allowlist. Use TLS and a reverse proxy rate limit in front.

## Claude Code layers (this repo's `.claude/`)

1. **Sandbox / devcontainer.** Run agents with broad permissions only in a sandbox. Never use `--dangerously-skip-permissions` outside one.
2. **Deny rules are tripwires.** `Read(.env)` and friends stop casual leaks, but Bash deny rules can be bypassed (`/bin/rm`, `sh -c`). They are not a boundary.
3. **Hooks.** `danger-guard.sh` blocks destructive shell patterns, `secret-scan.sh` blocks key-shaped content in edits (exit 2 holds in every permission mode). Both are pattern matches: they catch accidents, not attackers.
4. **Untrusted repos.** Project `permissions.allow` rules wait for workspace trust, but a skill's `allowed-tools` does not. Read a cloned repo's `.claude/` before opening it in Claude Code.
5. **Skills, plugins, MCP servers run with your permissions.** Read every `SKILL.md` and script, pin to a commit, install from one source (not also an aggregator copy), run `/doctor prompt-audit` afterwards.
6. **Secrets.** gitleaks in CI; `.env` ignored; the secret-scan hook; keys only via environment.

## If a secret leaks

Rotate first, then remove it from history, then find out how it got there.
