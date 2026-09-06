from dataclasses import dataclass

from flowchartmaker.domain.branch import Branch
from flowchartmaker.domain.nodes import Node


class EmptyInputError(Exception):
    """Raised before any LLM call, when text input is empty/whitespace-only or no image was provided."""


class SketchUnreadableError(Exception):
    """Raised by the vision stage when it cannot produce a confident Sketch description from an image.

    `reason` is human-readable and written for direct end-user display.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


@dataclass
class ValidationFailure:
    """One specific problem found during Flowchart validation."""

    def describe(self) -> str:
        raise NotImplementedError


@dataclass
class MultipleStartNodesFailure(ValidationFailure):
    nodes: list[Node]

    def describe(self) -> str:
        labels = ", ".join(f"'{n.label}' (id={n.id})" for n in self.nodes)
        return f"Multiple StartNodes found: {labels}. A Flowchart must have exactly one StartNode."


@dataclass
class MissingStartNodeFailure(ValidationFailure):
    def describe(self) -> str:
        return "No StartNode found. A Flowchart must have exactly one StartNode."


@dataclass
class MissingEndNodeFailure(ValidationFailure):
    def describe(self) -> str:
        return "No EndNode found. A Flowchart must have exactly one EndNode."


@dataclass
class MultipleEndNodesFailure(ValidationFailure):
    nodes: list[Node]

    def describe(self) -> str:
        labels = ", ".join(f"'{n.label}' (id={n.id})" for n in self.nodes)
        return f"Multiple EndNodes found: {labels}. A Flowchart must have exactly one EndNode."


@dataclass
class DanglingReferenceFailure(ValidationFailure):
    edge: Branch

    def describe(self) -> str:
        return (
            f"Branch from '{self.edge.source_id}' to '{self.edge.target_id}' "
            f"(label={self.edge.label!r}) references a node id that does not exist."
        )


@dataclass
class UnreachableNodeFailure(ValidationFailure):
    nodes: list[Node]

    def describe(self) -> str:
        labels = ", ".join(f"'{n.label}' (id={n.id})" for n in self.nodes)
        return f"Node(s) not reachable from the StartNode: {labels}."


@dataclass
class DuplicateNodeIdFailure(ValidationFailure):
    nodes: list[Node]

    def describe(self) -> str:
        labels = ", ".join(f"'{n.label}' (id={n.id})" for n in self.nodes)
        return f"Multiple nodes share the same id: {labels}. Each node must have a unique id."


class FlowchartValidationError(Exception):
    """Raised when a Flowchart fails structural validation.

    Carries every `ValidationFailure` found in one validation pass (not just the first),
    so both an LLM self-correction retry loop and, on exhaustion, a user-facing message
    can be driven from the same aggregate.
    """

    def __init__(self, failures: list[ValidationFailure]) -> None:
        self.failures = failures
        super().__init__(self.to_llm_feedback())

    def to_llm_feedback(self) -> str:
        return "\n".join(f"- {failure.describe()}" for failure in self.failures)
