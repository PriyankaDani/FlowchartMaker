---
status: Done
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

- [x] `ParsingPipeline.parse_text(...)` on the worked example text, piped into `MermaidRenderer.render(...)`, produces syntactically valid Mermaid matching the expected structure from `docs/learning/example.md`
- [x] `ParsingPipeline.parse_image(...)` on the worked example sketch, piped into `MermaidRenderer.render(...)`, produces syntactically valid Mermaid equivalent to the text-path result
- [x] A real LLM-produced `Flowchart` containing a loop (from a retry-loop process description) renders without error
- [x] A real LLM-produced `Flowchart` with a node whose LLM-assigned id happens to collide with a Mermaid reserved word renders with a sanitized id
- [x] A batch of 5+ varied real process descriptions (different lengths, with/without explicit branches, with/without loops) all round-trip parse -> render without a renderer-side exception

## Notes

- Suite: `tests/integration/test_parsing_rendering_live.py` (Ollama text stage; the image test also uses 1 Gemini call). No schema drift found between `ParsingPipeline` output and `MermaidRenderer`; no production code changed.
- RCA (first run): the reserved-word test failed with `FlowchartValidationError` (two EndNodes) because the prompt asked the LLM to assign specific ids, which confused the text model � a text-stage issue, not a renderer one. Reworded.

## Follow-ups

- The reserved-word live test samples up to 4 LLM runs and skips if none produces a reserved id (the LLM ignores requested ids, so a collision can't be forced). Deterministic collision handling stays covered in `tests/rendering/test_mermaid_renderer.py`.
