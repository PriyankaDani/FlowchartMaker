---
status: Done
component: domain
---

# 010 — Structured Validation Feedback

Enrich `FlowchartValidationError` and `SketchUnreadableError` so they carry enough structured/human-readable information to drive an LLM self-correction retry loop (`011`) and, on exhaustion, a graceful in-UI message — instead of today's flat, string-only exceptions.

## Entry Conditions

- `001_domain_model` — Done (defines `Flowchart`, its validators, and today's flat `FlowchartValidationError` / `DuplicateNodeIdError` / `SketchUnreadableError`)

## Tasks

- `domain/errors.py`:
  - `ValidationFailure`: plain data-class base (not `Exception`) for one specific validation problem. No forced uniform interface — each subclass exposes only the attribute(s) natural to its failure, referencing the actual offending `Node`/`Branch` objects (not just ids/labels):
    - `MultipleStartNodesFailure(nodes: list[Node])`
    - `MissingStartNodeFailure()`
    - `MissingEndNodeFailure()` / `MultipleEndNodesFailure(nodes: list[Node])`
    - `DanglingReferenceFailure(edge: Branch)` — edge references a non-existent node
    - `UnreachableNodeFailure(nodes: list[Node])`
    - `DuplicateNodeIdFailure(nodes: list[Node])`
  - `FlowchartValidationError(Exception)`: holds `failures: list[ValidationFailure]` (always the full set found in one validation pass — see below). Exposes `to_llm_feedback() -> str`, rendering every collected failure into one LLM-readable correction target (which nodes/labels/edges, what's wrong with each). This same string is reused as-is for end-user display after retries are exhausted (`011`) — no separate user-facing rendering.
  - `DuplicateNodeIdError` is removed as a standalone raisable/catchable exception type; its case becomes `DuplicateNodeIdFailure` inside the aggregate.
  - `SketchUnreadableError(reason: str)`: `reason` is required, human-readable, written for direct end-user display (the vision stage prompts its LLM to describe the issue and suggest a fix — that prompt work belongs to `003`, not this ticket). No rendering method — it's already display-ready text.
- `domain/flowchart.py`: collapse the existing four `@model_validator(mode="after")` methods (start/end counts, unique ids, edge references, reachability) into one pass that runs **all** checks and collects every `ValidationFailure` found, rather than stopping at the first. Raise one `FlowchartValidationError(failures=[...])` if the list is non-empty.

## Exit Conditions

All tests green against Ollama-independent unit tests (no LLM dependency in this ticket):

- [x] A `Flowchart` with two `StartNode`s raises `FlowchartValidationError` whose `.failures` contains a `MultipleStartNodesFailure` referencing both `StartNode` instances
- [x] A `Flowchart` missing a `StartNode` raises with a `MissingStartNodeFailure` in `.failures`
- [x] A `Flowchart` with zero/multiple `EndNode`s raises with the corresponding failure in `.failures`
- [x] A `Flowchart` with an edge referencing a non-existent node id raises with a `DanglingReferenceFailure` referencing the offending `Branch`
- [x] A `Flowchart` with an unreachable node raises with an `UnreachableNodeFailure` referencing the unreachable `Node`(s)
- [x] A `Flowchart` with two nodes sharing an `id` raises with a `DuplicateNodeIdFailure` referencing both `Node`s
- [x] A `Flowchart` with **multiple simultaneous** problems (e.g. two `StartNode`s *and* a duplicate id) raises **one** `FlowchartValidationError` whose `.failures` contains **both** failures — proves aggregation, not fail-fast
- [x] `FlowchartValidationError.to_llm_feedback()` on a multi-failure error produces text mentioning every failure's specifics (node ids/labels involved), not just the first
- [x] `Flowchart` containing a cycle (loop-back edge) still validates successfully (no regression on ADR 0002 behavior)
- [x] `SketchUnreadableError("...")` exposes `.reason` unchanged (string in, string out)
- [x] Existing worked-example and cycle/label tests in `tests/domain/test_domain_model.py` continue to pass, updated where they asserted the now-removed `DuplicateNodeIdError`

## RCA Notes

No failing tests were hit unexpectedly — the four `@model_validator(mode="after")` methods on `Flowchart` were collapsed into one `_validate` pass that builds a `list[ValidationFailure]` and raises once at the end, rather than raising on the first exception. `DuplicateNodeIdError` was removed; its case is now `DuplicateNodeIdFailure` inside the aggregate, matching the ticket's design intent. Each `ValidationFailure` subclass owns its own `describe()` method (dispatch by subclass, not by a central formatter), which is what `FlowchartValidationError.to_llm_feedback()` joins into one string reused as-is for end-user display after retries are exhausted.

## Follow-ups

- `011_llm_retry_loop` will consume `FlowchartValidationError.to_llm_feedback()` and the previous attempt's output to build retry prompts.
- `003_vision_parsing_chain` (not yet built) is responsible for actually populating `SketchUnreadableError.reason` with a well-written, suggestion-carrying message from its vision LLM call — this ticket only defines the shape.
- `002_text_parsing_chain` and `003_vision_parsing_chain`'s `Entry Conditions` should list this ticket once they're written/started.
