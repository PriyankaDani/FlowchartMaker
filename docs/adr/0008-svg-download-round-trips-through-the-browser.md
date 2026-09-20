# SVG download round-trips through the browser

`GET /download-svg` must return a valid SVG of the current diagram, but the app is Python-only and the Mermaid → SVG step is done by Mermaid.js, which needs a browser DOM. Rendering SVG server-side would mean a headless browser or Node dependency in the packaged `.exe`, which CLAUDE.md's stack rules out.

Decision: the browser renders the Mermaid syntax returned by `POST /parse`, then uploads the resulting SVG to `POST /svg`; the server keeps it in a single in-memory slot (`DiagramStore`) and `GET /download-svg` serves it as an attachment. Starting a new `/parse` clears the slot, so a stale diagram can't be downloaded; before any diagram exists, `/download-svg` returns 404 with a "nothing to download yet" message rather than a 500. `/svg` rejects bodies that aren't SVG.

Also: `mermaid.min.js` is vendored into `web/static/` rather than loaded from a CDN, so the packaged build works offline.

Consequences: server state is one slot, which suits a local single-user app but would need per-session storage for a hosted deploy (a later, separate ticket). The exit condition "download after a successful parse" is exercised as parse → SVG upload → download.
