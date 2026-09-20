import re

from flowchartmaker.domain.flowchart import Flowchart
from flowchartmaker.domain.nodes import Decision, EndNode, Node, StartNode


class MermaidRenderer:
    """Renders a Flowchart as Mermaid `flowchart TD` syntax. Pure and deterministic."""

    RESERVED = frozenset(
        {"end", "graph", "subgraph", "flowchart", "style", "class", "classdef",
         "click", "default", "linkstyle", "direction"}
    )

    def render(self, flowchart: Flowchart) -> str:
        ids = self._assign_ids(flowchart.nodes)
        lines = ["flowchart TD"]
        for node in flowchart.nodes:
            lines.append(f"    {ids[node.id]}{self._shape(node)}")
        for edge in flowchart.edges:
            arrow = f"-->|{self._label(edge.label)}|" if edge.label else "-->"
            lines.append(f"    {ids[edge.source_id]} {arrow} {ids[edge.target_id]}")
        return "\n".join(lines) + "\n"

    def _assign_ids(self, nodes: list[Node]) -> dict[str, str]:
        mapping: dict[str, str] = {}
        used: set[str] = set()
        for node in nodes:
            safe = re.sub(r"\W", "_", node.id) or "n"
            if safe.lower() in self.RESERVED:
                safe += "_node"
            candidate, i = safe, 2
            while candidate in used:
                candidate = f"{safe}_{i}"
                i += 1
            used.add(candidate)
            mapping[node.id] = candidate
        return mapping

    def _shape(self, node: Node) -> str:
        text = self._label(node.label)
        if isinstance(node, (StartNode, EndNode)):
            return f"([{text}])"
        if isinstance(node, Decision):
            return "{" + text + "}"
        return f"[{text}]"

    @staticmethod
    def _label(text: str) -> str:
        return text.replace('"', "#quot;").replace("|", "#124;")
