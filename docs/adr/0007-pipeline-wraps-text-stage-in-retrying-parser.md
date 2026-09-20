# `ParsingPipeline` wraps the text stage in `RetryingParser`

Ticket 006's live test (worked-example sketch vs. equivalent text) intermittently failed on the local Ollama model: the text chain emitted branches referencing node ids that don't exist, so `FlowchartValidationError` reached the caller. `RetryingParser` (ADR 0006, ticket 011) exists for exactly this, but the ticket didn't specify wiring it in.

Decision: `ParsingPipeline` wraps `TextParsingChain.parse` in `RetryingParser` for both input paths, rather than leaving callers (the web layer) to do so. The pipeline is the single entry point, so retry policy lives in one place. Vision-stage errors (`SketchUnreadableError`) are never retried; after retries are exhausted the last `FlowchartValidationError` surfaces unchanged, preserving the per-stage error taxonomy.

Consequence: a persistently failing input costs up to 3 text-LLM calls (default `max_retries=2`).

Also recorded: a "nonsensical sketch → `FlowchartValidationError`" live test is not achievable, since validation is structural and the LLM invents structure for unconnected shapes (see ticket 006 RCA).
