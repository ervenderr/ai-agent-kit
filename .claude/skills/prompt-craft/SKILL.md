---
name: prompt-craft
description: Write, review, or simplify prompts for Claude (system prompts, tool descriptions, skills, CLAUDE.md). Use when authoring or auditing any prompt text.
---
# Prompt craft

- State the goal, the audience, what "good" looks like, and only the constraints that are truly non-negotiable. Give the reason for each.
- Prefer judgment to rule lists. Newer Claude models are hurt by over-constraining; delete rules the model already follows.
- Say each thing once, in the right place. Tool guidance belongs in the tool description.
- Examples narrow exploration. Use them only where output format must be exact; give 2-3 diverse ones.
- Point to references (a schema, a test file, a sample output) instead of describing them.
- Separate instructions from data. Wrap untrusted content in tags and say it is data, not instructions.
- Specify output format explicitly and validate it in code.
- Keep prompts in `prompts/*.md`, versioned. Every change runs the evals; report the pass-rate diff.

Review checklist: contradictions, rules written for older models, secrets in the prompt (never), assumptions that the prompt stays private.
