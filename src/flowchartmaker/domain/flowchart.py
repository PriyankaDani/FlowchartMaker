from pydantic import BaseModel, model_validator

from flowchartmaker.domain.branch import Branch
from flowchartmaker.domain.errors import (
    DanglingReferenceFailure,
    DuplicateNodeIdFailure,
    FlowchartValidationError,
    MissingEndNodeFailure,
    MissingStartNodeFailure,
    MultipleEndNodesFailure,
    MultipleStartNodesFailure,
    UnreachableNodeFailure,
    ValidationFailure,
)
from flowchartmaker.domain.nodes import EndNode, Node, StartNode


class Flowchart(BaseModel):
    nodes: list[Node]
    edges: list[Branch]

    @model_validator(mode="after")
    def _validate(self) -> "Flowchart":
        failures: list[ValidationFailure] = []

        start_nodes = [n for n in self.nodes if isinstance(n, StartNode)]
        end_nodes = [n for n in self.nodes if isinstance(n, EndNode)]
        if not start_nodes:
            failures.append(MissingStartNodeFailure())
        elif len(start_nodes) > 1:
            failures.append(MultipleStartNodesFailure(nodes=start_nodes))
        if not end_nodes:
            failures.append(MissingEndNodeFailure())
        elif len(end_nodes) > 1:
            failures.append(MultipleEndNodesFailure(nodes=end_nodes))

        nodes_by_id: dict[str, list[Node]] = {}
        for node in self.nodes:
            nodes_by_id.setdefault(node.id, []).append(node)
        duplicate_nodes = [
            n for group in nodes_by_id.values() if len(group) > 1 for n in group
        ]
        if duplicate_nodes:
            failures.append(DuplicateNodeIdFailure(nodes=duplicate_nodes))

        node_ids = set(nodes_by_id.keys())
        for edge in self.edges:
            if edge.source_id not in node_ids or edge.target_id not in node_ids:
                failures.append(DanglingReferenceFailure(edge=edge))

        if start_nodes:
            adjacency: dict[str, list[str]] = {}
            for edge in self.edges:
                if edge.source_id in node_ids and edge.target_id in node_ids:
                    adjacency.setdefault(edge.source_id, []).append(edge.target_id)

            reachable: set[str] = set()
            stack = [start_nodes[0].id]
            while stack:
                current = stack.pop()
                if current in reachable:
                    continue
                reachable.add(current)
                stack.extend(adjacency.get(current, []))

            unreachable = [n for n in self.nodes if n.id not in reachable]
            if unreachable:
                failures.append(UnreachableNodeFailure(nodes=unreachable))

        if failures:
            raise FlowchartValidationError(failures)
        return self
