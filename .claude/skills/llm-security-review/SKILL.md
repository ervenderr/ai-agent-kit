---
name: llm-security-review
description: Security review of an LLM app or agent against the OWASP Top 10 for LLM Applications 2025. Use before merging agent, tool, RAG, or prompt changes, or when asked for a security review.
---
# LLM security review

The model is not a security boundary. Enforce everything in code. Answer for this repo with file:line:

- LLM01 Prompt injection: what untrusted text reaches the model (web, files, email, tool output, users)? What is the worst tool call it could cause? Capability limits are the real defence.
- LLM02 Sensitive info disclosure: what secrets or PII can the model see or echo? Logs?
- LLM03 Supply chain: pinned deps; vetted MCP servers, skills, plugins (they run with your permissions).
- LLM04 Poisoning: who can write to RAG stores or training data?
- LLM05 Improper output handling: is model output used in SQL, shell, HTML, paths, or URLs unvalidated?
- LLM06 Excessive agency: per tool, least privilege, confirmation for side effects, per-user authz in code.
- LLM07 System prompt leakage: no secrets or authz logic in prompts.
- LLM08 Vector/embedding weaknesses: tenant isolation in vector queries.
- LLM09 Misinformation: grounding, citations, human review where wrong answers cost money.
- LLM10 Unbounded consumption: per-user rate limits, token/cost/step caps, timeouts, request size limits.

Also classic web checks: authn/z, SSRF, CORS, CSRF, dependency audit, secrets in repo and CI.
Run the security-reviewer agent for a fresh-context pass. Report a table: finding, severity, file:line, fix. If nothing found, say what you checked.
