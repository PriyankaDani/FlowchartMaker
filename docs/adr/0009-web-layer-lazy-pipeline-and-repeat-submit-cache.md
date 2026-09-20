# Web layer builds the pipeline lazily, caches the last parse, and maps LLM outages to 503

Ticket 008 wires the real `ParsingPipeline` into Flask. Three decisions:

**Lazy pipeline.** `LLMProvider` probes Ollama (or checks the Gemini key) in its constructor and raises `LLMConfigurationError`. Building the pipeline at import/startup would crash the app before the browser could show anything. `LazyPipeline` builds it on first use instead, so the failure surfaces as a user-facing message on the first request. A failed build is not remembered, so starting Ollama and re-submitting works without a restart. `create_app(pipeline)` keeps its signature (tests inject mocks); `create_default_app()` is the real wiring.

**Repeat-submit cache.** `docs/projectbrief.md` requires that re-submitting identical input makes no second LLM call. `DiagramStore` remembers the Mermaid output for the most recent successful input only (text as-is, images by SHA-256). It lives in the web layer, not the pipeline: it's a UI concern (accidental double-click) and the app is single-user and local, matching the single SVG slot in ADR 0008. Failures are never cached. A cache hit still clears the stored SVG, so the browser re-renders and re-uploads it as usual.

**Error mapping.** `LLMConfigurationError`, `ConnectionError` and `httpx.TransportError` (Ollama stopped mid-session) return 503 with an "LLM isn't available" message. Any other exception returns a generic 500 message and is logged, so the browser never shows a stack trace. Domain errors keep their existing 400/422 mappings (ADR 0008).

Consequences: provider-specific runtime errors from Gemini (quota, auth) currently fall into the generic 500 message; distinguishing them is a possible later refinement. Hosted deploy would need per-session cache and SVG storage.
