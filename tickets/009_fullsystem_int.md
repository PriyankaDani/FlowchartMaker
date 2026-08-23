---
status: Todo
component: fullsystem_int
---

# 009 — Full System Integration (Packaged .exe)

Packages the app as a standalone PyInstaller `.exe` and proves the complete user journey works on a clean environment with no dev tooling installed, per `docs/projectbrief.md`'s form-factor requirement.

## Entry Conditions

- `008_web_pipeline_int` — Done

## Tasks

- `config.py`: `resource_path(relative: str) -> Path` helper — resolves bundled assets (`templates/`, `static/`) relative to `sys._MEIPASS` when frozen, and the `.env` relative to `sys.executable`'s directory (writable, editable, not inside the temp bundle); falls back to repo-relative paths in dev
- `main.py`: run Flask without the Werkzeug reloader/debug mode (`use_reloader=False`, `debug=False`), or switch to a production WSGI server (e.g. `waitress`) — the reloader re-execs the script on start, which breaks once there's no script, only a frozen `.exe`
- `packaging/app.spec`: PyInstaller spec — `datas` for `templates/`/`static/`, `hiddenimports` (or `--collect-all`) for LangChain/Pydantic's dynamic imports (expect a build-fix-rebuild cycle to discover the full list)
- `packaging/.env.example`: documents required configuration (API keys, provider selection), copied next to the built `.exe`
- Startup-time validation: missing/invalid API key detected before the UI is usable, with an explicit message naming what's missing and where to fix it (`.env`)
- README updated with setup/run instructions (per `CLAUDE.md`'s README rule — v1 conclusion)
- 30–60s screen recording/GIF for the README (per `docs/projectbrief.md` deliverable)

## Exit Conditions

- [ ] `.exe` builds successfully from a clean `uv sync` environment
- [ ] Running the `.exe` on a machine without Python/uv installed opens the browser UI at `localhost` (no reloader-related crash or duplicate process on launch)
- [ ] Templates and static assets render correctly from the frozen `.exe` (proves `resource_path()` resolves bundled assets correctly, not just in dev)
- [ ] `.env` placed next to the `.exe` is read correctly by the packaged app (proves `.env` resolves relative to `sys.executable`, not the temp bundle dir)
- [ ] Full user journey (text input) completes end-to-end from the packaged `.exe`, against Gemini (prod polish target, not Ollama — this is the one ticket where the Gemini pass is part of the exit condition, since it's the packaged/prod path)
- [ ] Full user journey (image input) completes end-to-end from the packaged `.exe`, against Gemini
- [ ] Missing `.env`/API key produces the documented explicit error message on startup, not a silent hang or crash
- [ ] SVG downloaded from the packaged `.exe` opens correctly in a browser/image viewer
- [ ] README setup instructions followed literally (by someone other than the implementer, or a fresh clone) result in a working run

## Follow-ups

- None expected at ticket creation time; if v1 scope items are deferred during this pass, list them here before closing rather than dropping silently (per `CLAUDE.md`).
