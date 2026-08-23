---
status: Todo
component: web_ui_shell
---

# 005 — Web UI Shell

The Flask app shell: input form (text or image upload), a render area, a loading state, and an error message area. Built and tested against a **mocked** pipeline (no real LLM/parsing/rendering wiring yet — that's `008_web_pipeline_int`).

## Entry Conditions

- None (buildable independently; only needs the *shape* of `ParseResult` / error types from `001_domain_model` to mock against)
- `001_domain_model` — Done (imports error types + `ParseResult` shape for mocking)

## Tasks

- `web/app.py`: Flask app factory
- `web/routes.py`:
  - `POST /parse` — accepts text or an uploaded image, calls an injected pipeline dependency (mocked in this ticket's tests), returns rendered result or error
  - `GET /download-svg` — returns the current diagram as an SVG file
- `web/templates/`: input form (text box + file upload), diagram render area, loading indicator, error message area
- `web/static/`: client-side Mermaid.js rendering of the returned syntax string, SVG export/download trigger
- Error-to-message mapping: `EmptyInputError` / `SketchUnreadableError` / `FlowchartValidationError` each map to distinct, user-facing copy (no stack traces surfaced to the browser)

## Exit Conditions

All tests green (mocked pipeline — no LLM calls, no Ollama dependency in this ticket):

- [ ] `POST /parse` with text input, mocked pipeline returning a successful `ParseResult`, returns a 200 with Mermaid syntax in the response
- [ ] `POST /parse` with image input, mocked pipeline returning a successful `ParseResult`, returns a 200 with Mermaid syntax in the response
- [ ] `POST /parse` with mocked pipeline raising `EmptyInputError` returns the empty-input-specific error message, no stack trace in response
- [ ] `POST /parse` with mocked pipeline raising `SketchUnreadableError` returns the sketch-unreadable-specific error message ("couldn't confidently read this sketch...")
- [ ] `POST /parse` with mocked pipeline raising `FlowchartValidationError` returns a generic malformed-input error message
- [ ] `GET /download-svg` after a successful parse returns a valid SVG file with the correct content-type/headers
- [ ] `GET /download-svg` before any successful parse returns a clear "nothing to download yet" response, not a 500
- [ ] The loading state is shown while `POST /parse` is in flight (verified via a slow-mocked pipeline + UI test, e.g. Playwright/Selenium checking the loading indicator's visibility)
