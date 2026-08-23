---
status: Todo
component: mermaid_renderer
---

# 004 — Mermaid Renderer

`MermaidRenderer`: `Flowchart` -> Mermaid flowchart syntax string, per the type-to-shape mapping documented in `docs/learning/example.md`.

## Entry Conditions

- `001_domain_model` — Done (renders `Flowchart` instances; no LLM dependency)

## Tasks

- `rendering/mermaid_renderer.py`: `MermaidRenderer.render(flowchart: Flowchart) -> str`
  - `StartNode`/`EndNode` -> stadium `([...])`
  - `Step` -> rectangle `[...]`
  - `Decision` -> diamond `{...}`
  - `Branch` with a label -> `-->|label|`
  - unlabeled edge -> plain `-->`
  - node ids sanitized against Mermaid reserved words (e.g. bare `end`) before emission

## Exit Conditions

All tests green (pure function, no LLM dependency — runs in any environment):

- [ ] Rendering the worked example `Flowchart` from `docs/learning/example.md` produces Mermaid output matching the documented expected output (structurally: same shapes, same edges, same labels — not necessarily byte-identical)
- [ ] A `Flowchart` containing a cycle renders without error (loop-back edge appears as a normal `-->` line)
- [ ] A `Flowchart` where two `Decision` branches converge on the same downstream node renders both incoming edges correctly (proves convergence, not duplicated node)
- [ ] A node with id `"end"` is rendered using a sanitized id (not the bare Mermaid-reserved `end`)
- [ ] Output is syntactically valid Mermaid (validated via a Mermaid parser/linter if available, or a golden-file round-trip render)
