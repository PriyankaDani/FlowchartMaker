"""Red-step tests for ticket 005 (web routes), with a mocked pipeline.

Assumed interface (design decisions recorded in ADR 0008):
- create_app(pipeline) -> Flask; pipeline exposes parse_text(str) / parse_image(bytes) -> ParseResult
- POST /parse: multipart/form-data with `text` field or `image` file. 200 -> {"mermaid": str};
  errors -> {"error": user-facing copy} with 400 (empty) / 422 (unreadable, invalid)
- POST /svg: the browser uploads the SVG it rendered from the Mermaid syntax (raw body)
- GET /download-svg: serves the last uploaded SVG as an attachment; 404 + message if none
"""
import io
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
from flowchartmaker.web.app import create_app

SVG = '<svg xmlns="http://www.w3.org/2000/svg"><rect width="1" height="1"/></svg>'


def _result() -> ParseResult:
    nodes = [StartNode(id="s", type="start", label="Start"), EndNode(id="e", type="end", label="End")]
    return ParseResult(
        flowchart=Flowchart(nodes=nodes, edges=[Branch(source_id="s", target_id="e")]),
        trace=ParseTrace(),
    )


@pytest.fixture
def pipeline():
    p = MagicMock()
    p.parse_text.return_value = _result()
    p.parse_image.return_value = _result()
    return p


@pytest.fixture
def client(pipeline):
    return create_app(pipeline).test_client()


def test_parse_text_returns_mermaid(client, pipeline):
    resp = client.post("/parse", data={"text": "do a thing"})

    assert resp.status_code == 200
    assert resp.get_json()["mermaid"].startswith("flowchart TD")
    pipeline.parse_text.assert_called_once_with("do a thing")


def test_parse_image_returns_mermaid(client, pipeline):
    resp = client.post("/parse", data={"image": (io.BytesIO(b"png-bytes"), "sketch.png")})

    assert resp.status_code == 200
    assert resp.get_json()["mermaid"].startswith("flowchart TD")
    pipeline.parse_image.assert_called_once_with(b"png-bytes")


@pytest.mark.parametrize(
    "exc, status, fragment",
    [
        (EmptyInputError("x"), 400, "Please enter"),
        (SketchUnreadableError("blurry"), 422, "couldn't confidently read this sketch"),
        (FlowchartValidationError(failures=[MissingEndNodeFailure()]), 422, "couldn't turn that into a valid flowchart"),
    ],
)
def test_pipeline_errors_map_to_distinct_messages(client, pipeline, exc, status, fragment):
    pipeline.parse_text.side_effect = exc

    resp = client.post("/parse", data={"text": "x"})

    assert resp.status_code == status
    body = resp.get_json()
    assert fragment in body["error"]
    assert "Traceback" not in resp.get_data(as_text=True)
    assert "MissingEndNode" not in body["error"] and "EndNode" not in body["error"]


def test_no_input_at_all_goes_to_pipeline_as_empty_text(client, pipeline):
    pipeline.parse_text.side_effect = EmptyInputError("x")

    resp = client.post("/parse", data={})

    assert resp.status_code == 400
    pipeline.parse_text.assert_called_once_with("")


def test_download_svg_after_parse_and_svg_upload(client):
    client.post("/parse", data={"text": "x"})
    assert client.post("/svg", data=SVG, content_type="image/svg+xml").status_code == 204

    resp = client.get("/download-svg")

    assert resp.status_code == 200
    assert resp.mimetype == "image/svg+xml"
    assert "attachment" in resp.headers["Content-Disposition"]
    assert ".svg" in resp.headers["Content-Disposition"]
    assert resp.get_data(as_text=True) == SVG


def test_download_svg_before_any_parse_is_clear_not_500(client):
    resp = client.get("/download-svg")

    assert resp.status_code == 404
    assert "nothing to download yet" in resp.get_json()["error"].lower()


def test_new_parse_invalidates_previous_svg(client):
    client.post("/svg", data=SVG, content_type="image/svg+xml")
    client.post("/parse", data={"text": "x"})

    assert client.get("/download-svg").status_code == 404


def test_svg_upload_rejects_non_svg(client):
    resp = client.post("/svg", data="<html>nope</html>", content_type="image/svg+xml")

    assert resp.status_code == 400
    assert client.get("/download-svg").status_code == 404


def test_index_page_has_form_loading_and_error_areas(client):
    html = client.get("/").get_data(as_text=True)

    for element_id in ("parse-form", "text-input", "image-input", "loading", "error", "diagram"):
        assert f'id="{element_id}"' in html


# --- ticket 008: LLM-unavailable mapping, repeat-submit caching, lazy pipeline ---

from flowchartmaker.llm.provider import LLMConfigurationError  # noqa: E402
from flowchartmaker.web.app import LazyPipeline  # noqa: E402


@pytest.mark.parametrize(
    "exc",
    [LLMConfigurationError("Could not reach Ollama at 'x'. Is Ollama running?"), ConnectionError("refused")],
)
def test_llm_unavailable_maps_to_503_message(client, pipeline, exc):
    pipeline.parse_text.side_effect = exc

    resp = client.post("/parse", data={"text": "x"})

    assert resp.status_code == 503
    assert "language model" in resp.get_json()["error"].lower()
    assert "Ollama at" not in resp.get_data(as_text=True)
    assert "Traceback" not in resp.get_data(as_text=True)


def test_unexpected_error_is_generic_500_not_a_stack_trace(client, pipeline):
    pipeline.parse_text.side_effect = RuntimeError("boom")

    resp = client.post("/parse", data={"text": "x"})

    assert resp.status_code == 500
    assert "boom" not in resp.get_data(as_text=True)
    assert resp.get_json()["error"]


def test_identical_text_resubmitted_does_not_call_pipeline_again(client, pipeline):
    first = client.post("/parse", data={"text": "do a thing"})
    second = client.post("/parse", data={"text": "do a thing"})

    assert first.get_json() == second.get_json()
    assert pipeline.parse_text.call_count == 1


def test_changed_text_calls_pipeline_again(client, pipeline):
    client.post("/parse", data={"text": "a"})
    client.post("/parse", data={"text": "b"})

    assert pipeline.parse_text.call_count == 2


def test_failed_parse_is_not_cached(client, pipeline):
    pipeline.parse_text.side_effect = [SketchUnreadableError("x"), _result()]

    assert client.post("/parse", data={"text": "a"}).status_code == 422
    assert client.post("/parse", data={"text": "a"}).status_code == 200


def test_identical_image_resubmitted_does_not_call_pipeline_again(client, pipeline):
    for _ in range(2):
        client.post("/parse", data={"image": (io.BytesIO(b"png"), "s.png")})

    assert pipeline.parse_image.call_count == 1


def test_cache_hit_still_invalidates_previous_svg(client):
    client.post("/parse", data={"text": "a"})
    client.post("/svg", data=SVG, content_type="image/svg+xml")
    client.post("/parse", data={"text": "a"})

    assert client.get("/download-svg").status_code == 404


def test_lazy_pipeline_builds_once_on_first_use():
    built = MagicMock()
    factory = MagicMock(return_value=built)
    lazy = LazyPipeline(factory)
    factory.assert_not_called()

    lazy.parse_text("a")
    lazy.parse_text("b")

    factory.assert_called_once()
    assert built.parse_text.call_count == 2


def test_lazy_pipeline_retries_build_after_config_failure():
    good = MagicMock()
    factory = MagicMock(side_effect=[LLMConfigurationError("down"), good])
    lazy = LazyPipeline(factory)

    with pytest.raises(LLMConfigurationError):
        lazy.parse_text("a")
    lazy.parse_text("a")

    good.parse_text.assert_called_once_with("a")
