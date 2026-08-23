---
status: Todo
component: web_pipeline_int
---

# 008 — Web + Pipeline Integration

Wires the real `ParsingPipeline` + `MermaidRenderer` into the Flask app from `005_web_ui_shell`, replacing the mocked pipeline dependency. Full browser-driven user journey, real LLM calls, real error surfacing.

## Entry Conditions

- `005_web_ui_shell` — Done
- `007_parsing_rendering_int` — Done

## Tasks

- Replace the mocked pipeline dependency in `web/routes.py` with the real `ParsingPipeline` + `MermaidRenderer`
- Confirm the loading state covers the actual LLM latency (not just the mocked delay from ticket 005)
- Confirm `.env` / config errors from `LLMProvider` (missing Ollama, missing Gemini key) surface as the startup/first-call message defined in `docs/projectbrief.md`, not a raw exception in the browser

## Exit Conditions

All tests green against Ollama; manually spot-check against Gemini before considering the polish pass done (non-blocking per `CLAUDE.md`):

- [ ] Full browser flow: type the worked example text -> submit -> loading state shown -> rendered diagram matches expected shape -> SVG download produces a valid file
- [ ] Full browser flow: upload the worked example clean sketch -> submit -> loading state shown -> rendered diagram matches expected shape -> SVG download produces a valid file
- [ ] Submitting empty text shows the empty-input message, no loading state hang, no stack trace
- [ ] Uploading a messy/illegible sketch shows the sketch-unreadable message
- [ ] Submitting gibberish text shows the malformed-input message
- [ ] With Ollama stopped (simulated LLM-unavailable), submitting text shows a clear "LLM unavailable" message, not a crash or frozen UI
- [ ] Re-submitting identical text without changes does not trigger a second LLM call (performance requirement from `docs/projectbrief.md`)
