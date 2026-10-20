@AGENTS.md

## Claude Code
- Plan mode first for changes to the agent loop, tool registry, auth or DB schema.
- Finish with evidence: test output, not a claim of success.
- Use subagents for broad exploration; keep the main session for implementation.
- `/clear` between unrelated tasks; `/context` when the session feels slow.
