"""Red-step tests for ticket 006 (ParsingPipeline), with mocked chains.

Assumed interface:
- ParsingPipeline(text_chain, vision_chain)
- parse_text(text) -> ParseResult; delegates to text_chain.parse
- parse_image(image) -> ParseResult; vision_chain.describe -> text_chain.parse,
  then trace.sketch_description is set to the description
- Errors from either stage propagate unchanged.
"""
from unittest.mock import MagicMock

import pytest

from flowchartmaker.domain.branch import Branch
from flowchartmaker.domain.errors import (
    EmptyInputError,
    FlowchartValidationError,
    MissingEndNodeFailure,
    SketchUnreadableError,
)
from flowchartmaker.domain.flowchart import Flowchart
from flowchartmaker.domain.nodes import EndNode, StartNode
from flowchartmaker.domain.trace import ParseResult, ParseTrace
from flowchartmaker.parsing.pipeline import ParsingPipeline


def _result() -> ParseResult:
    nodes = [StartNode(id="s", type="start", label="Start"), EndNode(id="e", type="end", label="End")]
    edges = [Branch(source_id="s", target_id="e", label="")]
    return ParseResult(flowchart=Flowchart(nodes=nodes, edges=edges), trace=ParseTrace())


@pytest.fixture
def text_chain():
    chain = MagicMock()
    chain.parse.return_value = _result()
    return chain


@pytest.fixture
def vision_chain():
    chain = MagicMock()
    chain.describe.return_value = "a start box, then an end box"
    return chain


def test_parse_text_delegates_and_has_no_sketch_description(text_chain, vision_chain):
    result = ParsingPipeline(text_chain, vision_chain).parse_text("do a thing")

    text_chain.parse.assert_called_once_with("do a thing")
    vision_chain.describe.assert_not_called()
    assert result.trace.sketch_description is None


def test_parse_image_feeds_description_into_text_chain(text_chain, vision_chain):
    result = ParsingPipeline(text_chain, vision_chain).parse_image(b"img")

    vision_chain.describe.assert_called_once_with(b"img")
    text_chain.parse.assert_called_once_with("a start box, then an end box")
    assert result.trace.sketch_description == "a start box, then an end box"


def test_sketch_unreadable_propagates_and_skips_text_chain(text_chain, vision_chain):
    vision_chain.describe.side_effect = SketchUnreadableError("scribble")

    with pytest.raises(SketchUnreadableError):
        ParsingPipeline(text_chain, vision_chain).parse_image(b"img")
    text_chain.parse.assert_not_called()


def test_validation_error_from_text_stage_propagates_unwrapped(text_chain, vision_chain):
    text_chain.parse.side_effect = FlowchartValidationError(failures=[MissingEndNodeFailure()])

    with pytest.raises(FlowchartValidationError):
        ParsingPipeline(text_chain, vision_chain).parse_image(b"img")


def test_empty_image_raises_before_vision_call(text_chain, vision_chain):
    with pytest.raises(EmptyInputError):
        ParsingPipeline(text_chain, vision_chain).parse_image(b"")
    vision_chain.describe.assert_not_called()


def test_text_stage_retries_on_validation_error_for_both_paths(text_chain, vision_chain):
    text_chain.parse.side_effect = [
        FlowchartValidationError(failures=[MissingEndNodeFailure()]),
        _result(),
        FlowchartValidationError(failures=[MissingEndNodeFailure()]),
        _result(),
    ]
    pipeline = ParsingPipeline(text_chain, vision_chain)

    pipeline.parse_text("do a thing")
    result = pipeline.parse_image(b"img")

    assert text_chain.parse.call_count == 4
    assert result.trace.sketch_description == "a start box, then an end box"
