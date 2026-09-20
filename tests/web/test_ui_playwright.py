"""Browser-level UI tests for ticket 005 (mocked, slow pipeline; no LLM)."""
import threading
import time
from unittest.mock import MagicMock

import pytest
from playwright.sync_api import Page, expect
from werkzeug.serving import make_server

from flowchartmaker.domain.branch import Branch
from flowchartmaker.domain.errors import SketchUnreadableError
from flowchartmaker.domain.flowchart import Flowchart
from flowchartmaker.domain.nodes import EndNode, StartNode
from flowchartmaker.domain.trace import ParseResult, ParseTrace
from flowchartmaker.web.app import create_app


def _result() -> ParseResult:
    nodes = [StartNode(id="s", type="start", label="Start"), EndNode(id="e", type="end", label="End")]
    return ParseResult(
        flowchart=Flowchart(nodes=nodes, edges=[Branch(source_id="s", target_id="e")]),
        trace=ParseTrace(),
    )


@pytest.fixture
def server():
    pipeline = MagicMock()

    def slow_parse(text):
        time.sleep(1.5)
        return _result()

    pipeline.parse_text.side_effect = slow_parse
    srv = make_server("127.0.0.1", 0, create_app(pipeline))
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{srv.server_port}", pipeline
    srv.shutdown()


def test_loading_indicator_visible_while_parse_in_flight(page: Page, server):
    url, _ = server
    page.goto(url)
    expect(page.locator("#loading")).to_be_hidden()

    page.fill("#text-input", "do a thing")
    page.click("button[type=submit]")

    expect(page.locator("#loading")).to_be_visible()
    expect(page.locator("#diagram svg")).to_be_visible(timeout=10_000)
    expect(page.locator("#loading")).to_be_hidden()
    expect(page.locator("#download")).to_be_visible()


def test_unreadable_sketch_error_shown_and_loading_cleared(page: Page, server):
    url, pipeline = server
    pipeline.parse_text.side_effect = SketchUnreadableError("blurry")
    page.goto(url)

    page.fill("#text-input", "x")
    page.click("button[type=submit]")

    expect(page.locator("#error")).to_contain_text("couldn't confidently read this sketch")
    expect(page.locator("#loading")).to_be_hidden()
    expect(page.locator("#diagram")).to_be_hidden()
