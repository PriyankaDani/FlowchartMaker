# FlowchartMaker

Turn a plain-text process description — or a photo of a hand-drawn sketch — into a clean, rendered [Mermaid.js](https://mermaid.js.org/) flowchart, downloadable as SVG. No Mermaid syntax knowledge required.

> **Status:** Pre-implementation. The domain model, parsing pipeline, and UI are still being built (see [Project Status](#project-status)). This README will grow setup/run instructions as those land, and a demo GIF will be added here once v1 is functional.

## What it does

- Accepts a free-text description of a process, or an image upload of a hand-drawn flowchart.
- Both input paths are parsed by an LLM into the same structured representation (steps, decisions, branches).
- The structured representation is rendered as a Mermaid flowchart in-browser.
- The rendered diagram can be downloaded as SVG.
- Malformed, empty, or ambiguous input produces a clear in-UI error instead of a bad diagram or a crash.

See [`docs/PRD.md`](docs/PRD.md) for target user and success criteria, and [`docs/projectbrief.md`](docs/projectbrief.md) for the full functional/non-functional requirements.

## Stack

- **Python only** — Streamlit UI, Mermaid rendering via component/HTML.
- **Pydantic** for structured/validated data (steps, decisions, branches, LLM output).
- **LangChain** for LLM orchestration (text and image parsing), so providers can be swapped without rewriting call logic.
- **Ollama** for local/test LLM calls (no cost, no rate limits); a Gemini API pass is used for polish/validation before a feature is considered fully done.
- **uv** for all environment and dependency management.
- Packaged as a local `.exe` via **PyInstaller** for v1 distribution.

## Project layout

See [`docs/code-structure.md`](docs/code-structure.md) for the full proposed package layout and how it maps to tickets. Key docs:

- [`CONTEXT.md`](CONTEXT.md) — domain model and terminology (`Flowchart`, `Node`, `Branch`, ...).
- [`docs/adr/`](docs/adr) — architectural decisions (e.g. why images are parsed via a text-description detour, why cycles are allowed).
- [`docs/learning/`](docs/learning) — worked examples tracing input through parsing to rendered output.
- [`tickets/`](tickets) — work items tracking implementation progress.

## Project status

Work is tracked as tickets in [`tickets/`](tickets). Current state:

| Ticket | Component | Status |
|---|---|---|
| [001](tickets/001_domain_model.md) | Domain model | Todo |
| [002](tickets/002_text_parsing_chain.md) | Text parsing chain | Todo |
| [003](tickets/003_vision_parsing_chain.md) | Vision parsing chain | Todo |
| [004](tickets/004_mermaid_renderer.md) | Mermaid renderer | Todo |
| [005](tickets/005_web_ui_shell.md) | Web UI shell | Todo |
| [006](tickets/006_text_vision_pipeline_int.md) | Text/vision pipeline integration | Todo |
| [007](tickets/007_parsing_rendering_int.md) | Parsing/rendering integration | Todo |
| [008](tickets/008_web_pipeline_int.md) | Web pipeline integration | Todo |
| [009](tickets/009_fullsystem_int.md) | Full-system integration (`.exe`) | Todo |

## Setup

Once the domain model and app scaffolding land (ticket 001+), this section will cover:

- Installing dependencies with `uv sync`
- Configuring `.env` (LLM provider selection, API keys) from a provided `.env.example`
- Running the app locally with `uv run`
- Running the local (Ollama) test suite with `uv run pytest`

## Out of scope (v1)

- Diagram types other than flowchart (sequence, ER, etc.)
- Auth, persistence, or saved diagrams
- Manual Mermaid-syntax editing
- Hosted/Vercel deployment (local `.exe` only for v1)

See [`docs/projectbrief.md`](docs/projectbrief.md) for the complete scope notes.
