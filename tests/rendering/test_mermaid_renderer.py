import re

import pytest

from flowchartmaker.domain.branch import Branch
from flowchartmaker.domain.flowchart import Flowchart
from flowchartmaker.domain.nodes import Decision, EndNode, StartNode, Step
from flowchartmaker.rendering.mermaid_renderer import MermaidRenderer

NODE_DEF = re.compile(r"(?P<id>[A-Za-z0-9_]+)(?P<open>\(\[|\[|\{)(?P<label>[^\]\}\)]*)(?:\]\)|\]|\})")
EDGE = re.compile(
    r"(?P<src>[A-Za-z0-9_]+)(?:\(\[[^\]]*\]\)|\[[^\]]*\]|\{[^\}]*\})?\s*-->"
    r"(?:\|(?P<label>[^|]*)\|)?\s*(?P<dst>[A-Za-z0-9_]+)"
)


def _worked_example() -> Flowchart:
    """From docs/learning/example.md."""
    return Flowchart(
        nodes=[
            StartNode(id="start", label="Start", type="start"),
            Step(id="n1", label="Check email", type="step"),
            Decision(id="n2", label="Urgent?", type="decision"),
            Step(id="n3", label="Reply now", type="step"),
            Step(id="n4", label="Add to queue", type="step"),
            EndNode(id="end1", label="End", type="end"),
        ],
        edges=[
            Branch(source_id="start", target_id="n1"),
            Branch(source_id="n1", target_id="n2"),
            Branch(source_id="n2", target_id="n3", label="Yes"),
            Branch(source_id="n2", target_id="n4", label="No"),
            Branch(source_id="n3", target_id="end1"),
            Branch(source_id="n4", target_id="end1"),
        ],
    )


def _defs(output: str) -> dict[str, tuple[str, str]]:
    """id -> (opening bracket, label), first definition wins."""
    defs: dict[str, tuple[str, str]] = {}
    for m in NODE_DEF.finditer(output):
        defs.setdefault(m["id"], (m["open"], m["label"]))
    return defs


def _edges(output: str) -> list[tuple[str, str | None, str]]:
    return [(m["src"], m["label"], m["dst"]) for m in EDGE.finditer(output)]


def test_output_starts_with_flowchart_header():
    out = MermaidRenderer().render(_worked_example())
    assert out.strip().splitlines()[0].strip() == "flowchart TD"


def test_worked_example_shapes():
    defs = _defs(MermaidRenderer().render(_worked_example()))
    assert defs["start"] == ("([", "Start")
    assert defs["n1"] == ("[", "Check email")
    assert defs["n2"] == ("{", "Urgent?")
    assert defs["n3"] == ("[", "Reply now")
    assert defs["n4"] == ("[", "Add to queue")
    assert defs["end1"] == ("([", "End")


def test_worked_example_edges_and_labels():
    edges = _edges(MermaidRenderer().render(_worked_example()))
    assert sorted(edges, key=str) == sorted(
        [
            ("start", None, "n1"),
            ("n1", None, "n2"),
            ("n2", "Yes", "n3"),
            ("n2", "No", "n4"),
            ("n3", None, "end1"),
            ("n4", None, "end1"),
        ],
        key=str,
    )


def test_unlabeled_edge_uses_plain_arrow():
    out = MermaidRenderer().render(_worked_example())
    assert "-->|" in out  # labeled ones exist
    assert not re.search(r"-->\|\s*\|", out)  # no empty label pipes
    assert "-->|None|" not in out


def test_cycle_renders_loop_back_edge():
    fc = Flowchart(
        nodes=[
            StartNode(id="s", label="Start", type="start"),
            Step(id="a", label="Do work", type="step"),
            Decision(id="d", label="OK?", type="decision"),
            EndNode(id="e1", label="Done", type="end"),
        ],
        edges=[
            Branch(source_id="s", target_id="a"),
            Branch(source_id="a", target_id="d"),
            Branch(source_id="d", target_id="a", label="No"),
            Branch(source_id="d", target_id="e1", label="Yes"),
        ],
    )
    edges = _edges(MermaidRenderer().render(fc))
    assert ("d", "No", "a") in edges
    assert ("d", "Yes", "e1") in edges


def test_convergence_renders_both_incoming_edges_without_duplicate_node():
    fc = _worked_example()
    out = MermaidRenderer().render(fc)
    edges = _edges(out)
    assert ("n3", None, "end1") in edges
    assert ("n4", None, "end1") in edges
    # the shared target is defined as a node exactly once
    assert len(re.findall(r"\bend1\(\[", out)) == 1


def test_reserved_word_end_id_is_sanitized():
    fc = Flowchart(
        nodes=[
            StartNode(id="start", label="Start", type="start"),
            Step(id="n1", label="Work", type="step"),
            EndNode(id="end", label="Finish", type="end"),
        ],
        edges=[
            Branch(source_id="start", target_id="n1"),
            Branch(source_id="n1", target_id="end"),
        ],
    )
    out = MermaidRenderer().render(fc)
    # bare lowercase `end` must never be used as an id
    assert not re.search(r"(?<![\w|])end(?![\w])(?=\s*(\(\[|\[|\{|-->|$))", out, re.M)
    defs = _defs(out)
    end_ids = [i for i, (o, l) in defs.items() if l == "Finish"]
    assert len(end_ids) == 1 and end_ids[0] != "end"
    # edge into the end node uses the sanitized id
    assert ("n1", None, end_ids[0]) in _edges(out)


def test_render_is_pure_and_deterministic():
    fc = _worked_example()
    r = MermaidRenderer()
    assert r.render(fc) == r.render(fc)


def test_output_lines_are_syntactically_well_formed():
    out = MermaidRenderer().render(_worked_example())
    for line in out.strip().splitlines()[1:]:
        line = line.strip()
        if not line:
            continue
        assert NODE_DEF.search(line) or EDGE.search(line), line
