"""Red-step tests for ticket 011 (RetryingParser).

Assumed interface (design decisions to confirm at green step):
- RetryingParser(parse_fn, max_retries=2); parse_fn: Callable[[str], ParseResult]
- RetryingParser.parse(text) -> ParseResult
- Retry attempts call parse_fn with a fresh single-string prompt embedding the previous
  attempt's raw output plus error.to_llm_feedback(). The raw output is read from the
  `raw_output` attribute of the raised FlowchartValidationError.
"""
from unittest.mock import MagicMock

import pytest

from flowchartmaker.domain.branch import Branch
from flowchartmaker.domain.errors import (
    FlowchartValidationError,
    MissingEndNodeFailure,
    MissingStartNodeFailure,
    SketchUnreadableError,
)
from flowchartmaker.domain.flowchart import Flowchart
from flowchartmaker.domain.nodes import EndNode, StartNode
from flowchartmaker.domain.trace import ParseResult, ParseTrace
from flowchartmaker.parsing.retry_loop import RetryingParser


def _result(sketch: str | None = None) -> ParseResult:
    nodes = [StartNode(id="s", type="start", label="Start"), EndNode(id="e", type="end", label="End")]
    edges = [Branch(source_id="s", target_id="e", label="")]
    return ParseResult(
        flowchart=Flowchart(nodes=nodes, edges=edges),
        trace=ParseTrace(sketch_description=sketch),
    )


def _error(failure, raw_output: str = "raw") -> FlowchartValidationError:
    err = FlowchartValidationError(failures=[failure])
    err.raw_output = raw_output
    return err


def test_first_attempt_success_returns_immediately_without_retry():
    ok = _result()
    parse_fn = MagicMock(return_value=ok)

    result = RetryingParser(parse_fn).parse("some text")

    assert result is ok
    parse_fn.assert_called_once_with("some text")


def test_retry_prompt_contains_previous_output_and_feedback():
    err = _error(MissingEndNodeFailure(), raw_output="PREVIOUS-RAW-OUTPUT")
    ok = _result()
    parse_fn = MagicMock(side_effect=[err, ok])

    result = RetryingParser(parse_fn).parse("original text")

    assert result is ok
    assert parse_fn.call_count == 2
    retry_prompt = parse_fn.call_args_list[1].args[0]
    assert isinstance(retry_prompt, str)
    assert "PREVIOUS-RAW-OUTPUT" in retry_prompt
    assert err.to_llm_feedback() in retry_prompt


def test_retry_prompt_is_stateless_not_accumulating_history():
    e1 = _error(MissingEndNodeFailure(), raw_output="OUT-1")
    e2 = _error(MissingStartNodeFailure(), raw_output="OUT-2")
    parse_fn = MagicMock(side_effect=[e1, e2, _result()])

    RetryingParser(parse_fn, max_retries=2).parse("original text")

    third_prompt = parse_fn.call_args_list[2].args[0]
    assert "OUT-2" in third_prompt
    assert e2.to_llm_feedback() in third_prompt
    assert "OUT-1" not in third_prompt


def test_exhaustion_reraises_last_error_unchanged():
    errors = [
        _error(MissingEndNodeFailure()),
        _error(MissingStartNodeFailure()),
        _error(MissingEndNodeFailure()),
    ]
    parse_fn = MagicMock(side_effect=errors)

    with pytest.raises(FlowchartValidationError) as exc_info:
        RetryingParser(parse_fn, max_retries=2).parse("text")

    assert exc_info.value is errors[-1]
    assert exc_info.value.failures == errors[-1].failures
    assert exc_info.value.to_llm_feedback() == errors[-1].to_llm_feedback()


@pytest.mark.parametrize("max_retries", [0, 1, 2, 5])
def test_max_retries_respected_exactly(max_retries):
    parse_fn = MagicMock(side_effect=lambda _p: (_ for _ in ()).throw(_error(MissingEndNodeFailure())))

    with pytest.raises(FlowchartValidationError):
        RetryingParser(parse_fn, max_retries=max_retries).parse("text")

    assert parse_fn.call_count == max_retries + 1


def test_default_max_retries_is_two():
    parse_fn = MagicMock(side_effect=lambda _p: (_ for _ in ()).throw(_error(MissingEndNodeFailure())))

    with pytest.raises(FlowchartValidationError):
        RetryingParser(parse_fn).parse("text")

    assert parse_fn.call_count == 3


def test_sketch_unreadable_error_propagates_unretried():
    err = SketchUnreadableError("too blurry")
    parse_fn = MagicMock(side_effect=err)

    with pytest.raises(SketchUnreadableError) as exc_info:
        RetryingParser(parse_fn, max_retries=3).parse("text")

    assert exc_info.value is err
    parse_fn.assert_called_once()


def test_same_class_serves_text_and_vision_shaped_callables():
    text_chain = MagicMock()
    text_chain.parse.side_effect = [_error(MissingEndNodeFailure()), _result()]
    vision_derived = MagicMock()
    vision_derived.parse.side_effect = [_error(MissingStartNodeFailure()), _result("a diamond...")]

    text_result = RetryingParser(text_chain.parse).parse("typed text")
    vision_result = RetryingParser(vision_derived.parse).parse("a diamond...")

    assert text_result.trace.sketch_description is None
    assert vision_result.trace.sketch_description == "a diamond..."
    assert text_chain.parse.call_count == 2
    assert vision_derived.parse.call_count == 2
