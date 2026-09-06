from unittest.mock import MagicMock

import pytest

from flowchartmaker.domain.errors import EmptyInputError, FlowchartValidationError
from flowchartmaker.domain.nodes import Decision, EndNode, StartNode, Step
from flowchartmaker.domain.branch import Branch
from flowchartmaker.domain.flowchart import Flowchart
from flowchartmaker.parsing.text_chain import TextParsingChain


def _fake_llm_provider(structured_output_return=None, side_effect=None):
    provider = MagicMock()
    structured_llm = MagicMock()
    if side_effect is not None:
        structured_llm.invoke.side_effect = side_effect
    else:
        structured_llm.invoke.return_value = structured_output_return
    provider.chat_model.with_structured_output.return_value = structured_llm
    return provider, structured_llm


def test_empty_string_raises_without_llm_call():
    provider, structured_llm = _fake_llm_provider()
    chain = TextParsingChain(provider)

    with pytest.raises(EmptyInputError):
        chain.parse("")

    structured_llm.invoke.assert_not_called()


def test_whitespace_only_raises_without_llm_call():
    provider, structured_llm = _fake_llm_provider()
    chain = TextParsingChain(provider)

    with pytest.raises(EmptyInputError):
        chain.parse("   \n\t  ")

    structured_llm.invoke.assert_not_called()


def test_valid_text_returns_parse_result_with_no_sketch_description():
    nodes, edges = _worked_example_nodes_edges()
    flowchart = Flowchart(nodes=nodes, edges=edges)
    provider, _ = _fake_llm_provider(structured_output_return=flowchart)
    chain = TextParsingChain(provider)

    result = chain.parse("Check email. If it's urgent, reply now. Otherwise, add it to the queue.")

    assert result.flowchart is flowchart
    assert result.trace.sketch_description is None


def test_flowchart_validation_error_propagates():
    provider, structured_llm = _fake_llm_provider(
        side_effect=FlowchartValidationError(failures=[])
    )
    chain = TextParsingChain(provider)

    with pytest.raises(FlowchartValidationError):
        chain.parse("gibberish qwerty asdf")


def _worked_example_nodes_edges():
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
