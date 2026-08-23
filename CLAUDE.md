# FlowchartMaker — Agent Instructions

## Project Map

- [`CONTEXT.md`](CONTEXT.md) — domain model: core entities (`Flowchart`, `Node`, `Branch`, ...) and the language to use for them. Read before touching parsing, validation, or the graph model.
- [`docs/`](docs) — requirements and product framing (problem, functional/non-functional requirements, scope, target user, user stories, success criteria). Read this first on any new task.
- [`docs/code-structure.md`](docs/code-structure.md) — proposed package layout, component responsibilities, and the ticket each maps to. Read before creating tickets or placing new code — it's the layout tickets are built against, not a suggestion.
- [`docs/adr/`](docs/adr) — one file per architectural decision. Check before changing a decision that looks arbitrary — it likely isn't.
- [`docs/learning/`](docs/learning) — worked examples tracing input through parsing to rendered output.
- `tickets/` — work items, one file per ticket (see Tickets below). Created as the plan is broken down.
- `README.md` — setup/run instructions, maintained per the README rule below.
- More docs will be added and linked here as they're created — check this list each session rather than assuming it's stale.

## Stack

- Python only: Streamlit for the app UI (Mermaid rendering via component/HTML), packaged as a local `.exe` (PyInstaller) for v1. No JS/Node layer.
- Distribution for v1: `.exe` + demo video in repo. Vercel/hosted deploy is a later, separate ticket — don't build toward it prematurely.

## Environment — uv

- All Python environment and dependency management goes through `uv` (`uv add`, `uv remove`, `uv sync`, `uv run`). Never call `pip` or manage a venv by hand.
- OOP throughout, per the project brief: class-based design, no loose script logic. No pinned Python version yet — don't invent one.

## README

- Create `README.md` at project start if it doesn't exist, and check/update it once v1 concludes.
- At all other times, only touch the README when explicitly asked.

## TDD

Red-green-refactor, in that order: write the failing test, then the implementation, then run tests.

- Test framework: `pytest`.
- Local iteration runs against Ollama (no cost, no rate limits).
- A failing test triggers root-cause analysis before any fix is attempted. Report the RCA in chat, and also append a short RCA note to the ticket file.
- A ticket's tests are green (Ollama) before the ticket is closed. The separate Gemini polish/validation pass (per the project brief) is a later, independent concern — it does not block closing the ticket.

## Tickets

- The plan is broken into work items, each documented as `tickets/NNN_workitemtocomplete.md` (zero-padded sequential number, e.g. `001_setup_uv_env.md`).
- Each ticket carries YAML frontmatter with at least a `status` field: `Todo`, `In Progress`, or `Done`.
- Closing a ticket: once its tests run green, update the ticket. If open sub-items remain that can't be completed now, flag them explicitly in the ticket (a `## Follow-ups` section is fine) before setting `status: Done` — don't silently drop scope.
- **Mid-ticket architectural decisions:** if a real decision gets made while implementing (not just following the plan), write an ADR for it in `docs/adr/` before closing the ticket — don't let it live only in code or chat history.

## Commits

Only commit when asked. One commit per logical unit of work — e.g. a method + its test + a doc update for the same change belongs in one commit. Don't bundle unrelated changes together, but don't split one coherent change across multiple commits either.

**Format:**
- Ticket-linked work: `TYPE:NNN brief description of work done/major change`
- Ticket-independent work: `TYPE:brief description of work done/major change`

**TYPE:**
| Type | Use for |
|---|---|
| `DOC` | Documentation |
| `FEAT` | Code tied to a ticket |
| `TEST` | Tests |
| `MOD` | Code change with no associated ticket |

**Flow:**
1. List every file to be committed for the ticket (or the standalone change) with its planned message.
2. Ask for confirmation once, covering the whole batch.
3. On confirmation, make the commits (one per logical unit).
4. Push only after a separate explicit go-ahead.