---
status: Todo
component: text_vision_pipeline_int
---

# 006 — Text + Vision Pipeline Integration

Wires `TextParsingChain` (002) and `VisionParsingChain` (003) together into `ParsingPipeline`, the single entry point the UI will call. Proves the ADR 0001 seam: image input funnels through the vision chain's description into the *same* text chain used for typed input, and the error taxonomy holds correctly at that seam.

## Entry Conditions

- `002_text_parsing_chain` — Done
- `003_vision_parsing_chain` — Done

## Tasks

- `parsing/pipeline.py`: `ParsingPipeline`
  - `parse_text(text: str) -> ParseResult` — delegates directly to `TextParsingChain`
  - `parse_image(image: bytes) -> ParseResult` — calls `VisionParsingChain.describe`, then feeds the resulting description into `TextParsingChain.parse`; the returned `ParseResult.trace` carries the `Sketch description`
  - error propagation: `SketchUnreadableError` from the vision stage surfaces as-is (not wrapped/converted); a downstream `FlowchartValidationError` on the generated description surfaces as-is too — no error-type conversion happens at this seam

## Exit Conditions

All tests green against Ollama (text model + vision-capable model):

- [ ] `parse_image` on the worked-example clean sketch produces a `Flowchart` structurally equivalent to `parse_text` on the equivalent worked-example text (proves both paths converge on the same representation)
- [ ] `parse_image` on a messy/illegible sketch raises `SketchUnreadableError` (raised by the vision stage, never reaches the text chain)
- [ ] `parse_image` on a sketch that describes cleanly but ambiguously (vision stage succeeds, but the resulting description is nonsensical/unparseable as a process) raises `FlowchartValidationError`, not `SketchUnreadableError` — proves the error-type boundary is per-stage, not per-input-type
- [ ] `ParseResult.trace.sketch_description` is populated and non-empty for the image path
- [ ] `ParseResult.trace.sketch_description` is `None`/absent for the text path
- [ ] No image bytes passed to `parse_image` raises `EmptyInputError` before the vision LLM is called
