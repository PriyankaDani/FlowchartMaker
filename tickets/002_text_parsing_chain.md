---
status: Todo
component: text_parsing_chain
---

# 002 — Text Parsing Chain

`TextParsingChain`: free text -> `Flowchart`, via a LangChain call with structured output validated against the `Flowchart` Pydantic schema. Includes the `LLMProvider` (Ollama for local/test, Gemini for polish) and prompt-injection-resistant prompt template.

## Entry Conditions

- `001_domain_model` — Done (uses `Flowchart`, `Branch`, `Node` types; raises `FlowchartValidationError`, `EmptyInputError`)

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

- [ ] Empty string input raises `EmptyInputError` without making an LLM call (assert no LLM invocation via mock/spy)
- [ ] Whitespace-only input raises `EmptyInputError`
- [ ] The worked example text from `docs/learning/example.md` ("Check email. If it's urgent...") parses into a `Flowchart` matching the expected node/edge shape (correct count of `Step`/`Decision`/`Branch`, correct `Branch` labels)
- [ ] A process description with no explicit "start"/"end" wording still produces a `Flowchart` with exactly one `StartNode` and one `EndNode` (proves implicit start/end inference)
- [ ] A process description containing a retry/loop ("if rejected, go back to step 2") parses into a `Flowchart` with a loop-back edge, and validates successfully
- [ ] Gibberish/unparseable input raises `FlowchartValidationError`
- [ ] Input containing an injection attempt ("ignore previous instructions and output...") does not alter the system prompt's behavior — output is still a valid `Flowchart` describing the literal input text, or a `FlowchartValidationError`, never arbitrary unrelated output
- [ ] Missing/invalid LLM configuration (bad Ollama URL, missing Gemini API key) raises a clear configuration error at `LLMProvider` construction, not a stack trace
