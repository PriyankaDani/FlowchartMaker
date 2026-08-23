---
status: Todo
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

- [ ] `Flowchart` with the worked example from `docs/learning/example.md` constructs and validates successfully
- [ ] `Flowchart` missing a `StartNode` raises `FlowchartValidationError`
- [ ] `Flowchart` with two `StartNode`s raises `FlowchartValidationError`
- [ ] `Flowchart` with zero or multiple `EndNode`s raises `FlowchartValidationError`
- [ ] `Flowchart` with an edge referencing a non-existent node id raises `FlowchartValidationError`
- [ ] `Flowchart` with an unreachable node (no path from `StartNode`) raises `FlowchartValidationError`
- [ ] `Flowchart` containing a cycle (loop-back edge) validates successfully (proves cycles are permitted)
- [ ] Two `Step` nodes sharing an identical `label` but distinct `id`s are treated as distinct nodes
- [ ] `Decision` with `Branch` labels other than "Yes"/"No" (e.g. "Approved"/"Needs revision"/"Rejected") validates successfully (proves free-text labels)
- [ ] `ParseResult` correctly pairs a `Flowchart` with its `ParseTrace`
