# Proposed Code Structure

This lays out the package layout tickets will be built against. It follows the domain model in `CONTEXT.md` and the pipeline shape from `docs/adr/0001-image-parsing-via-text-description-detour.md`.

Six components, each independently buildable/testable in isolation (mocked collaborators), then integrated in dependency order.

```
flowchartmaker/
  domain/
    nodes.py        # Node (base), StartNode, EndNode, Step, Decision
    branch.py         # Branch
    flowchart.py       # Flowchart aggregate + structural validators (reachability, single start/end)
    trace.py          # ParseTrace, ParseResult
    errors.py          # EmptyInputError, SketchUnreadableError, FlowchartValidationError

  llm/
    provider.py        # LLMProvider: instantiates Ollama (local/test) or Gemini (prod polish) via LangChain,
                        # validates API key/connectivity at startup, raises a clear error if misconfigured

  parsing/
    prompts.py         # Prompt templates; enforces the delimiter convention that separates
                        # untrusted user content from instructions (prompt-injection defense)
    text_chain.py       # TextParsingChain: free text -> Flowchart, via LangChain structured output,
                        # Pydantic-validated against the Flowchart schema
    vision_chain.py      # VisionParsingChain: sketch image -> free-form Sketch description (str),
                        # raises SketchUnreadableError on low-confidence read
    pipeline.py         # ParsingPipeline: single entry point used by the UI.
                        # routes text input directly to TextParsingChain;
                        # routes image input through VisionParsingChain, then TextParsingChain;
                        # both paths return ParseResult(flowchart, trace)

  rendering/
    mermaid_renderer.py  # MermaidRenderer: Flowchart -> Mermaid flowchart syntax (string),
                        # per the Node/Branch -> shape mapping in docs/learning/example.md

  web/
    app.py            # Flask app factory
    routes.py           # /parse (text or image upload), /download-svg
    templates/          # input form, Mermaid render area, loading state, error message area
    static/            # client-side mermaid.js render + SVG export/download

  config.py           # Settings: .env loading, LLM provider selection (Ollama vs Gemini), API key checks
                       # resolves paths (templates/static/.env) via resource_path() below,
                       # so behavior is identical in dev and frozen (.exe) mode
  main.py            # Entry point: launches Flask app (no reloader, no debug mode — see packaging notes)
                       # opens default browser to localhost. This is what PyInstaller packages into the .exe

packaging/
  app.spec            # PyInstaller spec: datas (templates/, static/), hiddenimports for
                       # langchain/pydantic dynamic imports, one-file vs one-dir mode
  hooks/              # custom PyInstaller hooks, only if trial builds show missing modules
  .env.example         # documents required config (API keys, provider selection) — copied
                       # next to the built .exe, not bundled inside it

tests/
  domain/
  parsing/
  rendering/
  web/
  integration/         # cross-component tests, mirrors the *_int tickets
```

## Component responsibilities (ticket mapping)

| Component | Module(s) | Depends on | Ticket |
|---|---|---|---|
| Domain model | `domain/` | — | `001_domain_model` |
| Text parsing chain | `parsing/text_chain.py`, `parsing/prompts.py`, `llm/provider.py` | Domain model | `002_text_parsing_chain` |
| Vision parsing chain | `parsing/vision_chain.py` | Domain model, `llm/provider.py` | `003_vision_parsing_chain` |
| Mermaid renderer | `rendering/mermaid_renderer.py` | Domain model | `004_mermaid_renderer` |
| Web UI shell | `web/` | — (built/tested against mocked pipeline output) | `005_web_ui_shell` |
| — | `parsing/pipeline.py` | Text chain + Vision chain | wired in `006_text_vision_pipeline_int` |

## Integration tickets

| Ticket | Integrates | What it proves |
|---|---|---|
| `006_text_vision_pipeline_int` | 002 + 003 | Image input funnels through the vision chain's `Sketch description` into the *same* text chain (ADR 0001) end-to-end; error taxonomy (`SketchUnreadableError` vs `FlowchartValidationError`) holds at the seam |
| `007_parsing_rendering_int` | 006 + 004 | A real `Flowchart` produced by either input path renders to valid Mermaid syntax |
| `008_web_pipeline_int` | 007 + 005 | The Flask app drives the full pipeline end-to-end in a browser: upload -> loading state -> rendered diagram -> SVG download, with stage-appropriate error messages surfaced from the domain error types |
| `009_fullsystem_int` | 008 + packaging | The PyInstaller `.exe` runs standalone on a clean environment and completes the full user journey (both input paths) |

`llm/provider.py` and `config.py` are cross-cutting (used by 002, 003, and startup) rather than components of their own — their behavior (API key validation, Ollama/Gemini switch) is covered as part of whichever ticket first depends on them (`002_text_parsing_chain`), and re-verified in `009_fullsystem_int` for the packaged/prod (Gemini) path.

## Packaging considerations (PyInstaller `.exe`)

These don't change the architecture above, but the components that touch the filesystem or process lifecycle need to behave identically in dev and frozen mode:

- **Resource path resolution.** `config.py` provides a `resource_path(relative: str) -> Path` helper: in dev, resolves relative to the repo; when frozen (`sys.frozen` set by PyInstaller), resolves relative to `sys._MEIPASS` for bundled read-only assets (`templates/`, `static/`) and relative to `sys.executable`'s directory for the `.env` (must be writable/editable next to the `.exe`, not inside the temp bundle).
- **Flask run mode.** `main.py` runs Flask without the Werkzeug reloader (`use_reloader=False`) and without debug mode — the reloader re-execs the "script" on start, which breaks once there's no script, only a frozen executable. A production WSGI server (e.g. `waitress`) is preferable to Flask's dev server for the packaged build.
- **LangChain/Pydantic hidden imports.** Both do dynamic/plugin-style imports PyInstaller's static analysis can miss. `packaging/app.spec` needs an explicit `hiddenimports` list (or `--collect-all langchain`, `--collect-all pydantic`), discovered by trial build rather than guessed upfront — expect at least one build-fix-rebuild cycle in `009_fullsystem_int`.
