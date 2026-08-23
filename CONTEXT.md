# FlowchartMaker

Converts a person's free-text process description or hand-drawn sketch into a validated, structured flowchart representation, which is then rendered as Mermaid/SVG.

## Language

### Core entities

**Flowchart**:
The root aggregate — a validated graph of nodes and branches produced by parsing user input. Holds a flat `nodes` list and a flat `edges` (branch) list, referenced by node ID rather than nested pointers, so convergence and loops can be represented. Exactly one `StartNode` and exactly one `EndNode`; every node must be reachable from the `StartNode`; cycles (retry/rework loops) are permitted.
_Avoid_: Diagram (reserved as a generic term for a future non-flowchart diagram type)

**Node**:
Base concept for anything that appears as a shape in the `Flowchart`. Has an `id` (assigned during parsing, used for edge references) distinct from its human-readable `label`. Two nodes may share a `label` and still be different nodes — reuse of an existing node requires an edge explicitly pointing back at its `id` (a loop), not a duplicate label.

**StartNode** / **EndNode**:
The single entry point and single exit point of a `Flowchart`. Always synthesized during parsing even when the user's input never uses the words "start" or "end" — inferring the beginning and end of a described process is part of the parsing step's job, the same way inferring a `Decision` from conditional phrasing is.

**Step**:
A `Node` representing a single action in the process, with exactly one outgoing edge.

**Decision**:
A `Node` representing a branching point, with one or more outgoing `Branch`es.
_Avoid_: Conditional, gateway

**Branch**:
A labeled edge originating from a `Decision` and pointing at a target `Node`. The label is free text (e.g. "Yes", "No", "Approved", "Needs revision") — not restricted to a binary vocabulary, since real decisions can have more than two outcomes.
_Avoid_: Edge, connection, transition (reserved for plain unlabeled `Step → Node` links, which are not branches)

### Parsing pipeline

**Sketch description**:
The free-form natural-language description a vision model produces from an uploaded sketch image (e.g. "a diamond asking 'Urgent?' with two arrows..."). Not itself structured — it is fed into the same text-parsing step used for typed input, so both input paths share one extraction chain. Never surfaced to the user or treated as part of the `Flowchart` model.

**ParseTrace**:
A record of a parsing run's intermediate state (currently: the `Sketch description`, when the input was an image), returned alongside the resulting `Flowchart` so tests can assert on pipeline behavior independent of final validation outcome.

### Failure modes

Distinct failure types, one per pipeline stage, so the UI can show stage-appropriate messaging:

**EmptyInputError**:
Raised before any LLM call, when text input is empty/whitespace-only or no image was provided.

**SketchUnreadableError**:
Raised by the vision stage when it cannot produce a confident `Sketch description` from an uploaded image. Never raised for typed text input.

**FlowchartValidationError**:
Raised when the text-parsing step's output fails Pydantic validation — for either input path, since a `Sketch description` is just text by the time it reaches this step. Ambiguous input that still produces a structurally valid `Flowchart` is *not* an error, even if the result may not match what the user intended.
