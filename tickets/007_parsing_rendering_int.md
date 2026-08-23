---
status: Todo
component: parsing_rendering_int
---

# 007 — Parsing + Rendering Integration

Proves a `Flowchart` produced by the real `ParsingPipeline` (either input path) renders to valid Mermaid syntax via `MermaidRenderer` — no mocked `Flowchart` fixtures, real LLM-produced structures.

## Entry Conditions

- `006_text_vision_pipeline_int` — Done
- `004_mermaid_renderer` — Done

## Tasks

- No new production code expected beyond wiring glue, if any (`MermaidRenderer.render(pipeline_result.flowchart)` in whatever calls both) — this ticket is primarily an integration test suite proving the two components compose without a shape mismatch
- Fix any schema drift discovered between what `ParsingPipeline` actually produces and what `MermaidRenderer` assumes

## Exit Conditions

All tests green against Ollama:

- [ ] `ParsingPipeline.parse_text(...)` on the worked example text, piped into `MermaidRenderer.render(...)`, produces syntactically valid Mermaid matching the expected structure from `docs/learning/example.md`
- [ ] `ParsingPipeline.parse_image(...)` on the worked example sketch, piped into `MermaidRenderer.render(...)`, produces syntactically valid Mermaid equivalent to the text-path result
- [ ] A real LLM-produced `Flowchart` containing a loop (from a retry-loop process description) renders without error
- [ ] A real LLM-produced `Flowchart` with a node whose LLM-assigned id happens to collide with a Mermaid reserved word renders with a sanitized id
- [ ] A batch of 5+ varied real process descriptions (different lengths, with/without explicit branches, with/without loops) all round-trip parse -> render without a renderer-side exception
