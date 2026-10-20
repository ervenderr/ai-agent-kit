# Prompts

- One file per prompt (`system.md`). The header comment (purpose, owner eval) is stripped before sending.
- The system prompt is static: no user content, no timestamps (they break prompt caching).
- Change workflow: edit, run `cd apps/api && uv run pytest ../../evals -m "not live" -q`, then `LIVE_EVALS=1 ... -m live`, and put the pass-rate diff in the PR.
- Tool guidance belongs in the tool's `description`, not here. See the `prompt-craft` skill.
