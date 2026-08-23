# PRD — FlowchartMaker
---

See [`projectbrief.md`](projectbrief.md) for the problem statement, functional/non-functional requirements, and scope. This document covers the product framing that file doesn't: who it's for, how they'll use it, and what "working" looks like.

## Target user

Someone who has a process in their head (or a napkin sketch of one) and wants a clean flowchart out of it without learning Mermaid syntax or a diagramming tool. Not a diagramming power user — if they wanted fine-grained manual control they'd already be in draw.io or Lucidchart. They want to describe or sketch once and get a usable diagram back.

## User stories

- As a user, I paste or type a description of a process, so that I get a rendered flowchart without writing Mermaid syntax myself.
- As a user, I upload a photo of a hand-drawn flowchart, so that I don't have to re-describe something I've already sketched.
- As a user, I get a clear error instead of a bad diagram when my input is too ambiguous, so that I know to clarify rather than trust a wrong result.
- As a user, I download the rendered diagram as SVG, so that I can drop it into a doc or slide.

## Success criteria

- A clearly-worded process description (the kind in `docs/learning/example.md`) produces a correct flowchart on the first try, no retry needed.
- A clean, legible hand-drawn sketch produces a flowchart matching the sketch's structure (same nodes, same branches).
- Ambiguous or malformed input produces a graceful in-UI error (per `projectbrief.md`'s Fallbacks section), never a stack trace or a silently wrong diagram.
- A user unfamiliar with Mermaid can go from "I have a process" to "I have a downloadable SVG" without reading documentation.

## Out of scope for success measurement

Anything listed under `projectbrief.md`'s "Explicitly Out of Scope" — multi-diagram-type support, auth/persistence, manual Mermaid editing — isn't part of v1's bar for "done."
