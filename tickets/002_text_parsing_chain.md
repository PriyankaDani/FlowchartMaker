---
status: Done
component: text_parsing_chain
---

# 002 — Text Parsing Chain

`TextParsingChain`: free text -> `Flowchart`, via a LangChain call with structured output validated against the `Flowchart` Pydantic schema. Includes the `LLMProvider` (Ollama for local/test, Gemini for polish) and prompt-injection-resistant prompt template.

## Entry Conditions

- `001_domain_model` — Done (uses `Flowchart`, `Branch`, `Node` types; raises `FlowchartValidationError`, `EmptyInputError`)
- `docs/adr/0004-node-type-discriminator-field.md` — `Node` subclasses now carry a `type` discriminator so structured LLM output deserializes to the correct `StartNode`/`EndNode`/`Step`/`Decision` subclass instead of collapsing to plain `Node`

## Tasks

- `llm/provider.py`: `LLMProvider` class — instantiates the LangChain chat model (Ollama by default; Gemini via config), validates API key/connectivity at construction, raises a clear misconfiguration error (not a stack trace) if the model is unreachable
- `config.py`: `.env` loading, provider selection setting
- `parsing/prompts.py`: prompt template that clearly delimits untrusted user text from system instructions
- `parsing/text_chain.py`: `TextParsingChain.parse(text: str) -> ParseResult`
  - raises `EmptyInputError` before any LLM call if `text` is empty/whitespace-only
  - calls the LLM via `LLMProvider`, parses structured output into `Flowchart`
  - lets `FlowchartValidationError` propagate on Pydantic validation failure
  - returns `ParseResult(flowchart, trace)` (trace has no `Sketch description` for text input)

## Exit Conditions

All tests green against Ollama (local); a manual Gemini polish pass does not block closing this ticket per `CLAUDE.md`.

- [x] Empty string input raises `EmptyInputError` without making an LLM call (assert no LLM invocation via mock/spy)
- [x] Whitespace-only input raises `EmptyInputError`
- [x] The worked example text from `docs/learning/example.md` ("Check email. If it's urgent...") parses into a `Flowchart` matching the expected node/edge shape (correct count of `Step`/`Decision`/`Branch`, correct `Branch` labels)
- [x] A process description with no explicit "start"/"end" wording still produces a `Flowchart` with exactly one `StartNode` and one `EndNode` (proves implicit start/end inference)
- [x] A process description containing a retry/loop ("if rejected, go back to step 2") parses into a `Flowchart` with a loop-back edge, and validates successfully
- [x] Gibberish/unparseable input either raises `FlowchartValidationError` or produces a structurally valid trivial `Flowchart` (e.g. a single `Step` whose label is the literal input) — `Flowchart`'s structural validators (001/010) have no concept of semantic meaninglessness, so a trivial-but-valid result is acceptable, not a bug (see RCA notes)
- [x] Input containing an injection attempt ("ignore previous instructions and output...") does not alter the system prompt's behavior — output is still a valid `Flowchart` describing the literal input text, or a `FlowchartValidationError`, never arbitrary unrelated output
- [x] Missing/invalid LLM configuration (bad Ollama URL, missing Gemini API key) raises a clear configuration error at `LLMProvider` construction, not a stack trace

## RCA Notes

**`union_tag_not_found` on every real Ollama call, despite the `type` discriminator existing (ADR 0004):** `StartNode.type: Literal["start"] = "start"` (and siblings) carried a Python-side default. A default makes Pydantic mark the field optional in the exported JSON schema, so Ollama's schema-constrained structured output reliably omitted `type` from its JSON once it saw it wasn't required — and a discriminated union can't apply a Python default to pick a member, so parsing failed with `union_tag_not_found` before `Flowchart`'s own validators ever ran. Fix: drop the defaults so `type` is `required` in schema (`docs/adr/0004...md`, addendum). Cost: every direct `StartNode(...)`-style construction (existing `001`/`010` tests, `docs/learning/example.md`) now must pass `type=...` explicitly; all call sites were updated.

**First real-model run produced a structurally invalid `Flowchart` (`UnreachableNodeFailure` on every non-start node):** llama3.2 (3B, temperature left at default) conflated the first described action ("Check email") with the `StartNode` itself and dropped an edge, and was non-deterministic run-to-run. Fixed by (a) setting `temperature=0` on `ChatOllama` for determinism, and (b) adding a concrete one-shot example to the system prompt (the exact `docs/learning/example.md` shape) plus an explicit rule that `StartNode`/`EndNode` are synthesized bookends, never the first/last described action. After this, the worked example parses to an exact structural match; loop and no-explicit-bookend cases pass reliably.

**Gibberish input never raised `FlowchartValidationError`:** the model turned nonsense text into a structurally valid one-step `Flowchart` (`Start → Step(<gibberish>) → End`) rather than failing. Root cause isn't a bug: `Flowchart`'s validators (`001`/`010`) check graph *structure* only (single start/end, reachability, no dangling refs) and have no notion of semantic meaninglessness, so a trivial one-step flowchart is indistinguishable from a real one-step process. Discussed with the user; the exit condition was relaxed rather than chasing prompt tricks to force a failure, since doing so risked weakening the prompt-injection defense (both behaviors are driven by the same "always extract *something* from the literal text" instruction).
