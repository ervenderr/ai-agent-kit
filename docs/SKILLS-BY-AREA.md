# Skills by area

Install 3-5 per project. Read every `SKILL.md` and its scripts first, pin to a commit, and run `/doctor prompt-audit` after adding. Names below were checked against each repository's file tree.

| Area | Skills | Repo |
|---|---|---|
| Agent building | `skill-creator`, `mcp-builder` (when exposing tools over MCP) | anthropics/skills |
| | Claude API / Agent SDK docs; bundled `/claude-api build-eval` for evals | - |
| Frontend design (one lead skill per task, at most two supporting; they conflict) | `frontend-design` | anthropics/skills |
| | `emil-design-eng` (polish, motion decisions) | emilkowalski/skills |
| | `impeccable` (critique, audit, polish; owns DESIGN.md) | pbakaus/impeccable |
| | `taste-skill` (only on explicit request) | Leonxlnx/taste-skill |
| | `react-best-practices`, `web-design-guidelines` | vercel-labs/agent-skills |
| Backend | `fastapi-expert`, `python-pro`, `api-designer` | Jeffallan/claude-skills |
| | `systematic-debugging`, `test-driven-development` | obra/superpowers |
| | `supabase-postgres-best-practices` | supabase/agent-skills |
| Workflow | `brainstorming`, `writing-plans`, `executing-plans`, `verification-before-completion`, `requesting-code-review` | obra/superpowers |
| Security | `static-analysis`, `differential-review`, `insecure-defaults`, `sharp-edges`, `supply-chain-risk-auditor`, `agentic-actions-auditor`; plus gitleaks in CI | trailofbits/skills |

Rules: never install a skill together with an aggregator copy of it, avoid unvetted mega-aggregators, and prefer this repo's own `new-tool`, `eval-suite`, `prompt-craft`, `llm-security-review` for agent work.
