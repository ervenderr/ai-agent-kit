---
name: eval-suite
description: Build or extend evals for an LLM feature (golden dataset, deterministic checks, replayed CI runs, judged rubrics, adversarial cases). Use when adding or changing prompts, tools, or agent behaviour.
---
# Evals for LLM features

Layers, cheapest first:
1. **Deterministic:** schema valid, expected tool called, steps under cap, forbidden strings absent. Always in CI.
2. **Replayed:** record real model responses once, replay in CI so tests are free and stable (pytest-based record/replay such as ghostrun).
3. **Judged:** rubric graded by a pinned judge model (promptfoo `llm-rubric` or DeepEval). Run on prompt changes and nightly; majority of 3 for flaky rubrics.
4. **Adversarial:** injection via retrieved text and tool output, jailbreaks, prompt-leak attempts, oversized input.

Rules:
- Golden cases in `evals/golden/*.jsonl`: id, input, expect (behaviour, not exact text), tags. Add every production failure as a case.
- `@pytest.mark.live` for real API calls; skipped unless `LIVE_EVALS=1`.
- Track pass rate, cost, latency, tokens per case; fail CI on regression past a stated threshold.
- A mock is not an eval; mocks test plumbing only.
- A failing eval means fix the prompt, tool, or code, never the test. Use the eval-triage agent to group failures by cause.

`/claude-api build-eval` and `/claude-api hillclimb` can bootstrap and tune an eval set for Claude-powered apps.
