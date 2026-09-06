---
status: Done
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

- [x] No image provided raises `EmptyInputError` without an LLM call
- [x] A clean, unambiguous sketch (matching the worked example diagram in `docs/learning/example.md`) produces a description that mentions all expected shapes (start, steps, decision with two labeled arrows, end) — asserted via keyword/content check, not exact string match
- [x] A messy/illegible sketch (scribbles, no discernible shapes) raises `SketchUnreadableError`
- [x] A photo containing no flowchart-like content at all (e.g. a blank page or unrelated photo) raises `SketchUnreadableError`
- [x] The returned description is a plain string — not asserted or coerced against the `Flowchart` schema at this stage (proves the "disposable, unstructured" boundary from ADR 0001)

## RCA — vision model choice (mid-ticket)

The "documented local equivalent" escape hatch in the exit conditions above ended up load-bearing. Three vision-capable Ollama models were tried locally and all failed for this ticket's purposes:

- `llava` (7B) and `llava:13b` load and run, but hallucinate: a genuinely blank image and a messy-scribble image were both confidently described as containing invented, plausible flowchart content instead of being flagged unreadable, and a real clean sketch got one hallucinated box that wasn't present. `llava:13b` was additionally too slow to return within 10 minutes on this hardware.
- `llama3.2-vision` fails to load at all (`unknown model architecture: 'mllama'`), reproduced even after confirming the installed Ollama build (`v0.33.3`) was already the latest release available — a real engine-support gap, not a stale-version issue.

`gemini-2.5-flash` was tried against the same three fixtures and passed all three on the first attempt (accurate grounded description of the clean sketch; correct `SketchUnreadableError` for both the blank page and scribble). Full writeup, including the rate-limit handling this implies for the test suite, in `docs/adr/0005-vision-chain-tested-against-gemini-not-ollama.md`.

## Follow-ups

- Local Ollama vision coverage is deferred — `tests/parsing/test_vision_chain_gemini.py` is the qualifying integration suite for now (skipped automatically if `GEMINI_API_KEY` isn't set). Revisit once a reliable, fast local vision model is available (see ADR 0005 for what would need to change).
- Bumped `Settings`' default `gemini_model` from `gemini-1.5-flash` (404s against current API) to `gemini-2.5-flash` as part of this ticket — affects `TextParsingChain`'s Gemini path too, not just vision.
