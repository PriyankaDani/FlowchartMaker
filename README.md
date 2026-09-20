# FlowchartMaker

Turn a plain-text process description — or a photo of a hand-drawn sketch — into a clean, rendered [Mermaid.js](https://mermaid.js.org/) flowchart, downloadable as SVG. No Mermaid syntax knowledge required.

> **Status:** v1 feature-complete; final packaging/verification of the Windows `.exe` is in progress (see [Project Status](#project-status)). A demo GIF will be added once the packaged build is verified end to end.

## What it does

- Accepts a free-text description of a process, or an image upload of a hand-drawn flowchart.
- Both input paths are parsed by an LLM into the same structured representation (steps, decisions, branches).
- The structured representation is rendered as a Mermaid flowchart in-browser.
- The rendered diagram can be downloaded as SVG.
- Malformed, empty, or ambiguous input produces a clear in-UI error instead of a bad diagram or a crash.

See [`docs/PRD.md`](docs/PRD.md) for target user and success criteria, and [`docs/projectbrief.md`](docs/projectbrief.md) for the full functional/non-functional requirements.

## Stack

- **Python only** — Flask UI, Mermaid.js rendering via static JS.
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
| [001](tickets/001_domain_model.md) | Domain model | Done |
| [002](tickets/002_text_parsing_chain.md) | Text parsing chain | Done |
| [003](tickets/003_vision_parsing_chain.md) | Vision parsing chain | Done |
| [004](tickets/004_mermaid_renderer.md) | Mermaid renderer | Done |
| [005](tickets/005_web_ui_shell.md) | Web UI shell | Done |
| [006](tickets/006_text_vision_pipeline_int.md) | Text/vision pipeline integration | In Progress |
| [007](tickets/007_parsing_rendering_int.md) | Parsing/rendering integration | Done |
| [008](tickets/008_web_pipeline_int.md) | Web pipeline integration | Done |
| [009](tickets/009_fullsystem_int.md) | Full-system integration (`.exe`) | In Progress |
| [010](tickets/010_structured_validation_feedback.md) | Structured validation feedback | Done |
| [011](tickets/011_llm_retry_loop.md) | LLM retry loop | Done |

## Setup (from source)

Requires [uv](https://docs.astral.sh/uv/). Do not use `pip` or manage a virtualenv by hand.

1. Install dependencies: `uv sync`
2. Create a `.env` in the repo root from the template: copy `packaging/.env.example` to `.env`, then set:
   - `LLM_PROVIDER` — `gemini` (default) or `ollama`.
   - `GEMINI_API_KEY` — required when `LLM_PROVIDER=gemini`. Optionally `GEMINI_MODEL` (default `gemini-2.5-flash`).
   - For Ollama: make sure Ollama is running; optionally set `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `OLLAMA_VISION_MODEL`.
3. Run the app: `uv run flowchartmaker`. It opens your browser on a free `127.0.0.1` port.

If the LLM configuration is missing or invalid, the app prints what is missing and where the `.env` should be, then exits with code 1.

Run the tests with `uv run pytest`. The live tests in `tests/integration/` drive a real browser and a real LLM (Chromium plus Ollama), so they are heavy and need those services available.

## Building the Windows `.exe`

1. `uv sync` (the dev group includes PyInstaller).
2. `uv run pyinstaller packaging/app.spec --noconfirm`
3. The output is a one-dir build at `dist/flowchartmaker/`. Keep the whole folder together; the entry point is `dist/flowchartmaker/flowchartmaker.exe`.
4. Copy `packaging/.env.example` to `dist/flowchartmaker/.env` (next to the exe) and fill it in, then run the exe.

The packaged app needs no Python or uv installed. Its `.env` is read from the folder containing the exe.

## Out of scope (v1)

- Diagram types other than flowchart (sequence, ER, etc.)
- Auth, persistence, or saved diagrams
- Manual Mermaid-syntax editing
- Hosted/Vercel deployment (local `.exe` only for v1)

See [`docs/projectbrief.md`](docs/projectbrief.md) for the complete scope notes.
