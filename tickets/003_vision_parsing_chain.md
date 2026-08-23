---
status: Todo
component: vision_parsing_chain
---

# 003 — Vision Parsing Chain

`VisionParsingChain`: sketch image -> free-form `Sketch description` (string). Per `docs/adr/0001-image-parsing-via-text-description-detour.md`, this component's only job is describing what it sees — it does not produce a `Flowchart` itself.

## Entry Conditions

- `001_domain_model` — Done (raises `SketchUnreadableError`, `EmptyInputError`)
- `002_text_parsing_chain` — Done (reuses `LLMProvider` from `llm/provider.py`)

## Tasks

- `parsing/vision_chain.py`: `VisionParsingChain.describe(image: bytes) -> str`
  - raises `EmptyInputError` before any LLM call if no image bytes are provided
  - calls a vision-capable LangChain model via `LLMProvider`
  - raises `SketchUnreadableError` when the model reports low confidence / cannot identify shapes or arrows
  - returns a free-form natural-language description (no structured extraction at this stage — ADR 0001)

## Exit Conditions

All tests green against Ollama's vision-capable model (or a documented local equivalent); Gemini polish pass is separate and non-blocking.

- [ ] No image provided raises `EmptyInputError` without an LLM call
- [ ] A clean, unambiguous sketch (matching the worked example diagram in `docs/learning/example.md`) produces a description that mentions all expected shapes (start, steps, decision with two labeled arrows, end) — asserted via keyword/content check, not exact string match
- [ ] A messy/illegible sketch (scribbles, no discernible shapes) raises `SketchUnreadableError`
- [ ] A photo containing no flowchart-like content at all (e.g. a blank page or unrelated photo) raises `SketchUnreadableError`
- [ ] The returned description is a plain string — not asserted or coerced against the `Flowchart` schema at this stage (proves the "disposable, unstructured" boundary from ADR 0001)
