---
name: new-agent
description: Design and scaffold an LLM agent or workflow (tool loop, hard caps, state, evals). Use when asked to build an AI agent, add an agentic feature, or choose between a workflow and an agent.
---
# Build an LLM agent

Start with the smallest design that works. Most features are a fixed workflow of 1-3 model calls, not an agent.

1. **Workflow or agent?** Fixed sequence of steps means workflow (chain, route, parallel calls). Tool choice depends on intermediate results means agent loop: gather context, act, verify, repeat.
2. **Caps live in code, not prompts.** Max tool calls (5-10 typical), wall time, tokens, per-run cost. Hitting a cap returns a clear failure; never auto-raise it.
3. **Tools:** few, narrow, clearly named. Return small structured results and errors the model can act on. A permission error is final; the agent must not route around it. Side-effecting tools need confirmation or an allowlist. Authorization is checked in code per user.
4. **State:** persist messages and tool results per run in Postgres so runs resume and replay. Log every tool call: args, result size, latency, error.
5. **Provider access** goes through one wrapper module (timeouts, retries, prompt caching, model choice, usage logging).
6. **Evals first.** Write 5-10 cases (2 adversarial) with the eval-suite skill, then implement until they pass.
7. **Framework last.** Plain SDK loop first. Add Pydantic AI or LangGraph for typed deps, checkpointing, or human-in-the-loop. Use the Claude Agent SDK when the agent needs files, shell, or a computer.
8. Run llm-security-review before merging.

Deliver: a one-page design in docs/ARCHITECTURE.md, the code, the evals.
