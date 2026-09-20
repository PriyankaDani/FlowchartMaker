# `FlowchartValidationError` carries an optional `raw_output`; the retry loop embeds it when present

Ticket 011's retry prompt must embed the previous attempt's raw LLM output. `FlowchartValidationError` is raised from `Flowchart` validation, which only sees parsed data and has no access to the LLM's raw text, so the error had no such field.

**Decision:** add `raw_output: str | None = None` to `FlowchartValidationError` (constructor kwarg, plain attribute). `RetryingParser` embeds it in the retry prompt, together with the original input text and `to_llm_feedback()`; if `None`, the prompt says the previous output is not available. Alternatives rejected: a wrapper exception (ticket requires re-raising the last error as-is); having the retry loop capture output itself (the loop wraps an opaque `parse_fn -> ParseResult` and never sees intermediate LLM output).

**Consequence:** the chains (`TextParsingChain`) do not yet populate `raw_output` — structured output hands them a parsed object or a pydantic error, not raw text. Populating it is a follow-up for ticket 006 wiring; until then retries carry the feedback and original text but not the prior output.

Baseline check: greps of CLAUDE.md, CONTEXT.md, projectbrief, PRD, code-structure and existing ADRs found no conflicting statement; `code-structure.md` updated to list `retry_loop.py`.
