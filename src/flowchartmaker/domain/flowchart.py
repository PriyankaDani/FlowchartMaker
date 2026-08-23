from pydantic import BaseModel, model_validator

from flowchartmaker.domain.branch import Branch
from flowchartmaker.domain.errors import DuplicateNodeIdError, FlowchartValidationError
from flowchartmaker.domain.nodes import EndNode, Node, StartNode


class Flowchart(BaseModel):
    nodes: list[Node]
    edges: list[Branch]

    @model_validator(mode="after")
    def _validate_start_and_end_counts(self) -> "Flowchart":
        start_count = sum(1 for n in self.nodes if isinstance(n, StartNode))
        end_count = sum(1 for n in self.nodes if isinstance(n, EndNode))
        if start_count != 1:
            raise FlowchartValidationError(
                f"Flowchart must have exactly one StartNode, found {start_count}"
            )
        if end_count != 1:
            raise FlowchartValidationError(
                f"Flowchart must have exactly one EndNode, found {end_count}"
            )
        return self

    @model_validator(mode="after")
    def _validate_unique_node_ids(self) -> "Flowchart":
        seen: set[str] = set()
        duplicates: set[str] = set()
        for node in self.nodes:
            if node.id in seen:
                duplicates.add(node.id)
            seen.add(node.id)
        if duplicates:
            raise DuplicateNodeIdError(
                f"Node id(s) used by more than one node: {sorted(duplicates)}"
            )
        return self

    @model_validator(mode="after")
    def _validate_edge_references(self) -> "Flowchart":
        node_ids = {n.id for n in self.nodes}
        for edge in self.edges:
            if edge.source_id not in node_ids:
                raise FlowchartValidationError(
                    f"Branch source_id '{edge.source_id}' does not reference a real node"
                )
            if edge.target_id not in node_ids:
                raise FlowchartValidationError(
                    f"Branch target_id '{edge.target_id}' does not reference a real node"
                )
        return self

    @model_validator(mode="after")
    def _validate_reachability(self) -> "Flowchart":
        start_node = next(n for n in self.nodes if isinstance(n, StartNode))
        end_node = next(n for n in self.nodes if isinstance(n, EndNode))

        adjacency: dict[str, list[str]] = {}
        for edge in self.edges:
            adjacency.setdefault(edge.source_id, []).append(edge.target_id)

        reachable: set[str] = set()
        stack = [start_node.id]
        while stack:
            current = stack.pop()
            if current in reachable:
                continue
            reachable.add(current)
            stack.extend(adjacency.get(current, []))

        if end_node.id not in reachable:
            raise FlowchartValidationError("EndNode is not reachable from StartNode")

        unreachable = {n.id for n in self.nodes} - reachable
        if unreachable:
            raise FlowchartValidationError(
                f"Node(s) not reachable from StartNode: {sorted(unreachable)}"
            )
        return self
