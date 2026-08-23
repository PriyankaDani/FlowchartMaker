class EmptyInputError(Exception):
    """Raised before any LLM call, when text input is empty/whitespace-only or no image was provided."""


class SketchUnreadableError(Exception):
    """Raised by the vision stage when it cannot produce a confident Sketch description from an image."""


class FlowchartValidationError(Exception):
    """Raised when a Flowchart fails structural validation (start/end count, edge references, reachability)."""


class DuplicateNodeIdError(FlowchartValidationError):
    """Raised when two or more nodes in a Flowchart share the same id."""
