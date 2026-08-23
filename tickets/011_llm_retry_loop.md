---
status: Todo
component: retry_loop
---

# 011 — LLM Retry Loop

A generic retry loop that wraps a "parse once" call, catches `FlowchartValidationError`, and re-prompts the LLM with structured feedback so it can self-correct — bounded by a max-retry count, falling back to surfacing the error once exhausted. Shared by both the text and vision-derived parsing paths, since both ultimately produce a `Flowchart` via the same text-parsing step (ADR 0001).

## Entry Conditions

- `010_structured_validation_feedback` — Done (defines `FlowchartValidationError.to_llm_feedback()`, which this ticket consumes)
- `002_text_parsing_chain` — Done (provides the `parse` callable this loop wraps)

## Tasks

- `parsing/retry_loop.py`: a class (e.g. `RetryingParser`) generic over any "parse once, raise `FlowchartValidationError` on failure" callable:
  - constructor takes `max_retries: int` with a sensible default (e.g. `2`) — not read from `config.py`; it's a call-level knob, not a deployment setting
  - on `FlowchartValidationError`, builds the next attempt's prompt as a **fresh, stateless** call (no multi-turn chat history) that embeds both the previous attempt's raw output and `error.to_llm_feedback()`
  - on success, returns the resulting `ParseResult`
  - on exhausting `max_retries`, re-raises the **last** `FlowchartValidationError` as-is (no new wrapper exception) — the caller/UI (`005`) displays `to_llm_feedback()` directly as the human-facing message
  - does **not** catch or retry `SketchUnreadableError` — that error is about the input image's clarity, not a correctable interpretation, so it propagates straight through to the caller/UI unchanged

## Exit Conditions

All tests green against Ollama (local); Gemini polish pass is separate and non-blocking.

- [ ] A parse call that succeeds on the first attempt returns immediately, no retry, no feedback sent
- [ ] A parse call that raises `FlowchartValidationError` on attempt 1 and succeeds on attempt 2 returns the successful `ParseResult`; the attempt-2 prompt is asserted to contain both the attempt-1 output and its `to_llm_feedback()` text
- [ ] A parse call that keeps raising `FlowchartValidationError` past `max_retries` re-raises the last `FlowchartValidationError` unchanged (same `.failures`, same `.to_llm_feedback()` output as the final underlying failure)
- [ ] `max_retries` is respected exactly — a failing call is attempted `max_retries + 1` times total, no more
- [ ] `SketchUnreadableError` raised by a wrapped call propagates immediately, unretried, unmodified — no additional LLM call is made
- [ ] The same `RetryingParser` class is exercised against both a stubbed text-chain-shaped callable and a stubbed vision-derived-text-chain-shaped callable, proving one shared implementation covers both input paths

## Follow-ups

- `docs/code-structure.md` doesn't yet list a retry/loop component — add `parsing/retry_loop.py` to the package layout and component-responsibility table once this ticket starts.
- `006_text_vision_pipeline_int` should confirm `RetryingParser` wraps the pipeline correctly for both the text and image input paths once wired.
