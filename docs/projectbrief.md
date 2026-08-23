# Project Brief — FlowchartMaker
---

## Problem

A person describes a process (text) or sketches a flowchart (image). The app converts either input into a clean, rendered Mermaid.js flowchart, downloadable as SVG.

---

## Form Factor

- Packaged as a local `.exe` (PyInstaller)
- Browser-based UI (Flask or Streamlit, opens on `localhost`) — not a native desktop window

---

## Functional Requirements

- Accepts free-text process description
- Accepts image upload (hand-drawn sketch of a flowchart)
- Both input paths produce the same structured intermediate representation (steps, decisions, branches)
- Converts structured representation into valid Mermaid syntax
- Renders Mermaid diagram in-browser
- Provides SVG download

---

## Non-Functional Requirements

### OOP
- Class-based design throughout (no loose script logic)

### Data validation — Pydantic
- All structured intermediate data (steps, decisions, branches) defined as Pydantic models, not raw dicts
- LLM output is validated against a Pydantic schema before it reaches the diagram contructor function so that malformed or unexpected LLM output should fail validation, not silently corrupt the diagram

### LLM orchestration — LangChain
- LLM calls (text parsing, image parsing) go through LangChain, not raw API calls
- Keeps the door open to swap models/providers later without rewriting call logic

### Testing — TDD + Ollama
- Red-green-refactor discipline, tests written before implementation
- Local testing against Ollama (no API cost, no rate limits, fast iteration loop)
- Final polish/validation pass against Gemini API before considering a feature "done"
- Test coverage should include: valid text input, valid clean-sketch image input, malformed/ambiguous input, empty input

### Security — Prompt injection resistance
- Treat all user input (text and OCR/vision-extracted text from images) as untrusted
- LLM prompts must clearly delimit user content from instructions, so injected text inside a description ("ignore previous instructions and...") can't hijack the parsing step
- Structured output (Pydantic validation) is itself a defense layer — even if injection partially succeeds, malformed output gets rejected before reaching the renderer

### Fallbacks — must degrade gracefully, not crash
- **LLM unavailable** (network down, Ollama not running, API down): clear in-UI error message, no stack trace shown to user
- **API key missing/invalid**: detected at startup or first call, explicit message telling the user what's missing and where to fix it (`.env` file)
- **Sketch unreadable** (messy handwriting, ambiguous arrows): graceful failure with a message like "couldn't confidently read this sketch — try a clearer photo or use text input instead," not a silent bad diagram or a crash

### Performance
- Rendering (Mermaid → SVG) should feel instant (local, no LLM involved)
- LLM parsing step is the bottleneck — UI should show a loading state, not appear frozen
- No unnecessary re-parsing: only re-call the LLM when input actually changes

---

## Explicitly Out of Scope (this weekend)

- Multiple diagram types (sequence, ER, etc.) — flowchart only
- Auth / persistence / saved diagrams
- Manual Mermaid-syntax editing (parked as a possible v2 escape hatch)

---

## Deliverable Beyond the Code

- README with setup instructions (`.env.example`, how to run)
- 30–60 second screen recording/GIF at the top of the README 
