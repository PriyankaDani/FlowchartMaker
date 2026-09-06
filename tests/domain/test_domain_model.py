import pytest

from flowchartmaker.domain.nodes import StartNode, EndNode, Step, Decision
from flowchartmaker.domain.branch import Branch
from flowchartmaker.domain.flowchart import Flowchart
from flowchartmaker.domain.trace import ParseTrace, ParseResult
from flowchartmaker.domain.errors import (
    DanglingReferenceFailure,
    DuplicateNodeIdFailure,
    FlowchartValidationError,
    MissingEndNodeFailure,
    MissingStartNodeFailure,
    MultipleEndNodesFailure,
    MultipleStartNodesFailure,
    SketchUnreadableError,
    UnreachableNodeFailure,
)


def _worked_example_nodes_edges():
    """From docs/learning/example.md."""
    nodes = [
        StartNode(id="start", label="Start", type="start"),
        Step(id="n1", label="Check email", type="step"),
        Decision(id="n2", label="Urgent?", type="decision"),
        Step(id="n3", label="Reply now", type="step"),
        Step(id="n4", label="Add to queue", type="step"),
        EndNode(id="end1", label="End", type="end"),
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
    with pytest.raises(FlowchartValidationError) as exc_info:
        Flowchart(nodes=nodes, edges=edges)
    failures = exc_info.value.failures
    assert any(isinstance(f, MissingStartNodeFailure) for f in failures)


def test_two_start_nodes_raises():
    nodes, edges = _worked_example_nodes_edges()
    start2 = StartNode(id="start2", label="Start2", type="start")
    nodes.append(start2)
    with pytest.raises(FlowchartValidationError) as exc_info:
        Flowchart(nodes=nodes, edges=edges)
    failures = exc_info.value.failures
    multi_start = next(f for f in failures if isinstance(f, MultipleStartNodesFailure))
    assert {n.id for n in multi_start.nodes} == {"start", "start2"}


def test_zero_end_nodes_raises():
    nodes, edges = _worked_example_nodes_edges()
    nodes = [n for n in nodes if not isinstance(n, EndNode)]
    edges = [e for e in edges if e.target_id != "end1"]
    with pytest.raises(FlowchartValidationError) as exc_info:
        Flowchart(nodes=nodes, edges=edges)
    failures = exc_info.value.failures
    assert any(isinstance(f, MissingEndNodeFailure) for f in failures)


def test_multiple_end_nodes_raises():
    nodes, edges = _worked_example_nodes_edges()
    nodes.append(EndNode(id="end2", label="End2", type="end"))
    edges.append(Branch(source_id="n3", target_id="end2", label=None))
    with pytest.raises(FlowchartValidationError) as exc_info:
        Flowchart(nodes=nodes, edges=edges)
    failures = exc_info.value.failures
    multi_end = next(f for f in failures if isinstance(f, MultipleEndNodesFailure))
    assert {n.id for n in multi_end.nodes} == {"end1", "end2"}


def test_edge_referencing_nonexistent_node_raises():
    nodes, edges = _worked_example_nodes_edges()
    ghost_edge = Branch(source_id="n4", target_id="ghost", label=None)
    edges.append(ghost_edge)
    with pytest.raises(FlowchartValidationError) as exc_info:
        Flowchart(nodes=nodes, edges=edges)
    failures = exc_info.value.failures
    dangling = next(f for f in failures if isinstance(f, DanglingReferenceFailure))
    assert dangling.edge == ghost_edge


def test_unreachable_node_raises():
    nodes, edges = _worked_example_nodes_edges()
    orphan = Step(id="orphan", label="Unreachable step", type="step")
    nodes.append(orphan)
    with pytest.raises(FlowchartValidationError) as exc_info:
        Flowchart(nodes=nodes, edges=edges)
    failures = exc_info.value.failures
    unreachable = next(f for f in failures if isinstance(f, UnreachableNodeFailure))
    assert {n.id for n in unreachable.nodes} == {"orphan"}


def test_cycle_validates_successfully():
    nodes, edges = _worked_example_nodes_edges()
    # Rework loop: queued email can loop back to "Check email".
    edges.append(Branch(source_id="n4", target_id="n1", label=None))
    flowchart = Flowchart(nodes=nodes, edges=edges)
    assert len(flowchart.edges) == 7


def test_distinct_ids_with_identical_labels_are_distinct_nodes():
    nodes, edges = _worked_example_nodes_edges()
    nodes.append(Step(id="n5", label="Reply now", type="step"))
    edges.append(Branch(source_id="n4", target_id="n5", label=None))
    edges.append(Branch(source_id="n5", target_id="end1", label=None))
    flowchart = Flowchart(nodes=nodes, edges=edges)
    reply_now_nodes = [n for n in flowchart.nodes if n.label == "Reply now"]
    assert len(reply_now_nodes) == 2
    assert reply_now_nodes[0].id != reply_now_nodes[1].id


def test_decision_with_non_yes_no_branch_labels_validates():
    nodes = [
        StartNode(id="start", label="Start", type="start"),
        Decision(id="n1", label="Review outcome?", type="decision"),
        Step(id="n2", label="Ship it", type="step"),
        Step(id="n3", label="Send back for edits", type="step"),
        Step(id="n4", label="Archive", type="step"),
        EndNode(id="end1", label="End", type="end"),
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
    nodes.append(Step(id="n1", label="Check email again", type="step"))
    edges.append(Branch(source_id="n4", target_id="n1", label=None))
    with pytest.raises(FlowchartValidationError) as exc_info:
        Flowchart(nodes=nodes, edges=edges)
    failures = exc_info.value.failures
    duplicate = next(f for f in failures if isinstance(f, DuplicateNodeIdFailure))
    assert len(duplicate.nodes) == 2
    assert all(n.id == "n1" for n in duplicate.nodes)


def test_multiple_simultaneous_failures_all_collected():
    nodes, edges = _worked_example_nodes_edges()
    nodes.append(StartNode(id="start2", label="Start2", type="start"))
    nodes.append(Step(id="n1", label="Check email again", type="step"))
    edges.append(Branch(source_id="n4", target_id="n1", label=None))
    with pytest.raises(FlowchartValidationError) as exc_info:
        Flowchart(nodes=nodes, edges=edges)
    failures = exc_info.value.failures
    assert any(isinstance(f, MultipleStartNodesFailure) for f in failures)
    assert any(isinstance(f, DuplicateNodeIdFailure) for f in failures)


def test_to_llm_feedback_mentions_every_failure():
    nodes, edges = _worked_example_nodes_edges()
    nodes.append(StartNode(id="start2", label="Start2", type="start"))
    nodes.append(Step(id="n1", label="Check email again", type="step"))
    edges.append(Branch(source_id="n4", target_id="n1", label=None))
    with pytest.raises(FlowchartValidationError) as exc_info:
        Flowchart(nodes=nodes, edges=edges)
    feedback = exc_info.value.to_llm_feedback()
    assert "start2" in feedback
    assert "n1" in feedback
    assert feedback.count("\n") >= 1


def test_sketch_unreadable_error_exposes_reason_unchanged():
    error = SketchUnreadableError("The sketch is too blurry to read; try a sharper photo.")
    assert error.reason == "The sketch is too blurry to read; try a sharper photo."


def test_parse_result_pairs_flowchart_with_trace():
    nodes, edges = _worked_example_nodes_edges()
    flowchart = Flowchart(nodes=nodes, edges=edges)
    trace = ParseTrace(sketch_description="a diamond asking 'Urgent?'...")
    result = ParseResult(flowchart=flowchart, trace=trace)
    assert result.flowchart is flowchart
    assert result.trace is trace
    assert result.trace.sketch_description.startswith("a diamond")
