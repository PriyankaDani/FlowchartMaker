import pytest

from flowchartmaker.domain.nodes import StartNode, EndNode, Step, Decision
from flowchartmaker.domain.branch import Branch
from flowchartmaker.domain.flowchart import Flowchart
from flowchartmaker.domain.trace import ParseTrace, ParseResult
from flowchartmaker.domain.errors import DuplicateNodeIdError, FlowchartValidationError


def _worked_example_nodes_edges():
    """From docs/learning/example.md."""
    nodes = [
        StartNode(id="start", label="Start"),
        Step(id="n1", label="Check email"),
        Decision(id="n2", label="Urgent?"),
        Step(id="n3", label="Reply now"),
        Step(id="n4", label="Add to queue"),
        EndNode(id="end1", label="End"),
    ]
    edges = [
        Branch(source_id="start", target_id="n1", label=None),
        Branch(source_id="n1", target_id="n2", label=None),
        Branch(source_id="n2", target_id="n3", label="Yes"),
        Branch(source_id="n2", target_id="n4", label="No"),
        Branch(source_id="n3", target_id="end1", label=None),
        Branch(source_id="n4", target_id="end1", label=None),
    ]
    return nodes, edges


def test_worked_example_constructs_and_validates():
    nodes, edges = _worked_example_nodes_edges()
    flowchart = Flowchart(nodes=nodes, edges=edges)
    assert len(flowchart.nodes) == 6
    assert len(flowchart.edges) == 6


def test_missing_start_node_raises():
    nodes, edges = _worked_example_nodes_edges()
    nodes = [n for n in nodes if not isinstance(n, StartNode)]
    with pytest.raises(FlowchartValidationError):
        Flowchart(nodes=nodes, edges=edges)


def test_two_start_nodes_raises():
    nodes, edges = _worked_example_nodes_edges()
    nodes.append(StartNode(id="start2", label="Start2"))
    with pytest.raises(FlowchartValidationError):
        Flowchart(nodes=nodes, edges=edges)


def test_zero_end_nodes_raises():
    nodes, edges = _worked_example_nodes_edges()
    nodes = [n for n in nodes if not isinstance(n, EndNode)]
    edges = [e for e in edges if e.target_id != "end1"]
    with pytest.raises(FlowchartValidationError):
        Flowchart(nodes=nodes, edges=edges)


def test_multiple_end_nodes_raises():
    nodes, edges = _worked_example_nodes_edges()
    nodes.append(EndNode(id="end2", label="End2"))
    edges.append(Branch(source_id="n3", target_id="end2", label=None))
    with pytest.raises(FlowchartValidationError):
        Flowchart(nodes=nodes, edges=edges)


def test_edge_referencing_nonexistent_node_raises():
    nodes, edges = _worked_example_nodes_edges()
    edges.append(Branch(source_id="n4", target_id="ghost", label=None))
    with pytest.raises(FlowchartValidationError):
        Flowchart(nodes=nodes, edges=edges)


def test_unreachable_node_raises():
    nodes, edges = _worked_example_nodes_edges()
    nodes.append(Step(id="orphan", label="Unreachable step"))
    with pytest.raises(FlowchartValidationError):
        Flowchart(nodes=nodes, edges=edges)


def test_cycle_validates_successfully():
    nodes, edges = _worked_example_nodes_edges()
    # Rework loop: queued email can loop back to "Check email".
    edges.append(Branch(source_id="n4", target_id="n1", label=None))
    flowchart = Flowchart(nodes=nodes, edges=edges)
    assert len(flowchart.edges) == 7


def test_distinct_ids_with_identical_labels_are_distinct_nodes():
    nodes, edges = _worked_example_nodes_edges()
    nodes.append(Step(id="n5", label="Reply now"))
    edges.append(Branch(source_id="n4", target_id="n5", label=None))
    edges.append(Branch(source_id="n5", target_id="end1", label=None))
    flowchart = Flowchart(nodes=nodes, edges=edges)
    reply_now_nodes = [n for n in flowchart.nodes if n.label == "Reply now"]
    assert len(reply_now_nodes) == 2
    assert reply_now_nodes[0].id != reply_now_nodes[1].id


def test_decision_with_non_yes_no_branch_labels_validates():
    nodes = [
        StartNode(id="start", label="Start"),
        Decision(id="n1", label="Review outcome?"),
        Step(id="n2", label="Ship it"),
        Step(id="n3", label="Send back for edits"),
        Step(id="n4", label="Archive"),
        EndNode(id="end1", label="End"),
    ]
    edges = [
        Branch(source_id="start", target_id="n1", label=None),
        Branch(source_id="n1", target_id="n2", label="Approved"),
        Branch(source_id="n1", target_id="n3", label="Needs revision"),
        Branch(source_id="n1", target_id="n4", label="Rejected"),
        Branch(source_id="n2", target_id="end1", label=None),
        Branch(source_id="n3", target_id="end1", label=None),
        Branch(source_id="n4", target_id="end1", label=None),
    ]
    flowchart = Flowchart(nodes=nodes, edges=edges)
    labels = {e.label for e in flowchart.edges if e.label}
    assert labels == {"Approved", "Needs revision", "Rejected"}


def test_duplicate_node_ids_raises():
    nodes, edges = _worked_example_nodes_edges()
    nodes.append(Step(id="n1", label="Check email again"))
    edges.append(Branch(source_id="n4", target_id="n1", label=None))
    with pytest.raises(DuplicateNodeIdError):
        Flowchart(nodes=nodes, edges=edges)


def test_parse_result_pairs_flowchart_with_trace():
    nodes, edges = _worked_example_nodes_edges()
    flowchart = Flowchart(nodes=nodes, edges=edges)
    trace = ParseTrace(sketch_description="a diamond asking 'Urgent?'...")
    result = ParseResult(flowchart=flowchart, trace=trace)
    assert result.flowchart is flowchart
    assert result.trace is trace
    assert result.trace.sketch_description.startswith("a diamond")
