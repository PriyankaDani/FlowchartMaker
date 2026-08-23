---
status: Done
component: domain
---

# 001 — Domain Model

Pydantic-based domain model: `Node` hierarchy, `Branch`, `Flowchart` aggregate, `ParseTrace`, and the error taxonomy. This is the foundation every other component builds on.

## Entry Conditions

- `uv` environment initialized (`pyproject.toml`, `uv sync` runs clean)
- `CONTEXT.md` and `docs/adr/0002-flowcharts-allow-cycles.md`, `docs/adr/0003-graph-model-with-id-referenced-edges.md` read (defines the shape this ticket implements)

## Tasks

- `domain/nodes.py`: `Node` base (`id: str`, `label: str`), `StartNode`, `EndNode`, `Step`, `Decision`
- `domain/branch.py`: `Branch` (`source_id`, `target_id`, `label: str | None`)
- `domain/flowchart.py`: `Flowchart` (`nodes: list[Node]`, `edges: list[Branch]`) with validators:
  - exactly one `StartNode`, exactly one `EndNode`
  - every `edge.source_id` / `edge.target_id` resolves to a real node id
  - every node reachable from `StartNode`; `EndNode` reachable from `StartNode`
  - cycles permitted (do not reject on cycle detection — ADR 0002)
- `domain/trace.py`: `ParseTrace` (holds intermediate `Sketch description` when present), `ParseResult` (`flowchart`, `trace`)
- `domain/errors.py`: `EmptyInputError`, `SketchUnreadableError`, `FlowchartValidationError`

## Exit Conditions

All tests green against Ollama-independent unit tests (this component has no LLM dependency):

- [x] `Flowchart` with the worked example from `docs/learning/example.md` constructs and validates successfully
- [x] `Flowchart` missing a `StartNode` raises `FlowchartValidationError`
- [x] `Flowchart` with two `StartNode`s raises `FlowchartValidationError`
- [x] `Flowchart` with zero or multiple `EndNode`s raises `FlowchartValidationError`
- [x] `Flowchart` with an edge referencing a non-existent node id raises `FlowchartValidationError`
- [x] `Flowchart` with an unreachable node (no path from `StartNode`) raises `FlowchartValidationError`
- [x] `Flowchart` containing a cycle (loop-back edge) validates successfully (proves cycles are permitted)
- [x] Two `Step` nodes sharing an identical `label` but distinct `id`s are treated as distinct nodes
- [x] `Decision` with `Branch` labels other than "Yes"/"No" (e.g. "Approved"/"Needs revision"/"Rejected") validates successfully (proves free-text labels)
- [x] `ParseResult` correctly pairs a `Flowchart` with its `ParseTrace`
- [x] `Flowchart` with two nodes sharing the same `id` raises `DuplicateNodeIdError` (folded in after discussion: an LLM generating node ids per-branch, or reusing an id instead of pointing an edge back at an existing node, is a plausible structured-output failure mode — not just a hypothetical edge case)

## Implementation Notes

- `uv` environment was not yet initialized at ticket start (`pyproject.toml` didn't exist) — created via `uv init --package`, then `uv add pydantic` and `uv add --dev pytest`. Left `requires-python = ">=3.11"` as a floor rather than keeping uv's auto-pinned exact `3.14`, since CLAUDE.md says not to invent a pinned version.
- Package lives at `src/flowchartmaker/domain/` (src-layout, uv's default) rather than a top-level `flowchartmaker/` — matches `code-structure.md`'s module contents, not its literal tree root.
- `Node`/`Branch`/`Flowchart` are plain Pydantic models; `Flowchart` validates via three `model_validator(mode="after")` hooks (start/end counts, edge reference integrity, reachability via DFS from `StartNode`). Subclass identity (`StartNode` vs `Node`) survives Pydantic's list-of-base-type validation because Pydantic v2 uses instances as-is when they already satisfy the annotated type.
- All 12 exit-condition tests pass against Ollama-independent unit tests only (no LLM dependency in this ticket, per plan) — `uv run pytest` green.
- `_validate_unique_node_ids` added after ticket close discussion surfaced a gap: the original three validators had no id-uniqueness check, so two distinct `Step`s sharing an `id` would silently collapse into one entry in `_validate_edge_references`'s `node_ids` set and never be caught. Runs before edge-reference/reachability checks so a duplicate is reported directly rather than surfacing as a confusing downstream reachability failure.
- Duplicate ids get their own `DuplicateNodeIdError(FlowchartValidationError)` rather than reusing the base error directly — it's a distinct enough failure (LLM structured-output id collision) from the other structural failures (missing start/end, bad edge reference, unreachable node) that the UI/caller may want to message it differently, while still being catchable as `FlowchartValidationError` by anything that only cares about the general category.
