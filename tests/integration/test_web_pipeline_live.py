"""Flask app + real ParsingPipeline, driven through a browser (ticket 008).

Text stage runs on local Ollama. Image tests also need Gemini for the vision stage
(ADR 0005) and are skipped without GEMINI_API_KEY; each costs 1 Gemini call.
"""
import threading
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect
from werkzeug.serving import make_server

from flowchartmaker.config import Settings
from flowchartmaker.llm.provider import LLMProvider
from flowchartmaker.parsing.pipeline import ParsingPipeline
from flowchartmaker.parsing.text_chain import TextParsingChain
from flowchartmaker.parsing.vision_chain import VisionParsingChain
from flowchartmaker.web.app import LazyPipeline, create_app, create_default_app

FIXTURES = Path(__file__).resolve().parents[1] / "parsing" / "fixtures"
WORKED_EXAMPLE = "Check email. If it's urgent, reply now. Otherwise, add it to the queue."
LLM_TIMEOUT = 180_000

needs_gemini = pytest.mark.skipif(
    not Settings().gemini_api_key, reason="GEMINI_API_KEY not set; vision stage needs Gemini."
)


def _serve(app):
    srv = make_server("127.0.0.1", 0, app)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def _mixed_pipeline() -> ParsingPipeline:
    gemini = Settings()
    gemini.llm_provider = "gemini"
    return ParsingPipeline(TextParsingChain(LLMProvider()), VisionParsingChain(LLMProvider(gemini)))


@pytest.fixture(scope="module")
def counting_pipeline():
    """Real text+vision pipeline that counts calls, so tests can assert on LLM usage."""
    real = LazyPipeline(_mixed_pipeline)

    class Counting:
        text_calls = 0

        def parse_text(self, text):
            self.text_calls += 1
            return real.parse_text(text)

        def parse_image(self, image):
            return real.parse_image(image)

    return Counting()


@pytest.fixture
def url(counting_pipeline):
    srv = _serve(create_app(counting_pipeline))
    yield f"http://127.0.0.1:{srv.server_port}"
    srv.shutdown()


def _assert_worked_example_diagram(page: Page):
    svg = page.locator("#diagram svg")
    expect(svg).to_be_visible(timeout=LLM_TIMEOUT)
    expect(page.locator("#loading")).to_be_hidden()
    text = (svg.text_content() or "").lower()
    assert "start" in text or "check email" in text
    assert svg.locator(".edgeLabel").count() >= 2  # the two decision branches
    expect(page.locator("#download")).to_be_visible()


def _assert_download_is_valid_svg(page: Page, tmp_path):
    with page.expect_download() as info:
        page.click("#download")
    path = tmp_path / "out.svg"
    info.value.save_as(path)
    content = path.read_text(encoding="utf-8")
    assert "<svg" in content and "</svg>" in content


def test_text_flow_end_to_end(page: Page, url, tmp_path):
    page.goto(url)
    page.fill("#text-input", WORKED_EXAMPLE)
    page.click("button[type=submit]")

    expect(page.locator("#loading")).to_be_visible()  # real LLM latency is seconds
    _assert_worked_example_diagram(page)
    _assert_download_is_valid_svg(page, tmp_path)


@needs_gemini
def test_image_flow_end_to_end(page: Page, url, tmp_path):
    page.goto(url)
    page.set_input_files("#image-input", str(FIXTURES / "clean_sketch.png"))
    page.click("button[type=submit]")

    expect(page.locator("#loading")).to_be_visible()
    _assert_worked_example_diagram(page)
    _assert_download_is_valid_svg(page, tmp_path)


def test_empty_text_shows_empty_input_message(page: Page, url):
    page.goto(url)
    page.click("button[type=submit]")

    expect(page.locator("#error")).to_contain_text("Please enter")
    expect(page.locator("#loading")).to_be_hidden()
    assert "Traceback" not in page.content()


@needs_gemini
def test_messy_sketch_shows_unreadable_message(page: Page, url):
    page.goto(url)
    page.set_input_files("#image-input", str(FIXTURES / "messy_scribble.png"))
    page.click("button[type=submit]")

    expect(page.locator("#error")).to_contain_text("couldn't confidently read", timeout=LLM_TIMEOUT)
    expect(page.locator("#loading")).to_be_hidden()


def test_gibberish_text_ends_in_message_or_diagram_never_a_hang_or_trace(page: Page, url):
    # Ticket 002 RCA: the model turns nonsense into a valid trivial flowchart, which is accepted;
    # the malformed-input message is the other acceptable outcome. Either way: no hang, no trace.
    page.goto(url)
    page.fill("#text-input", "asdf qwerty zxcv 1234 !!!! lorem ??")
    page.click("button[type=submit]")

    page.wait_for_selector("#error:not([hidden]), #diagram svg", timeout=LLM_TIMEOUT)
    expect(page.locator("#loading")).to_be_hidden()
    if page.locator("#error").is_visible():
        expect(page.locator("#error")).to_contain_text("couldn't turn that into a valid flowchart")
    assert "Traceback" not in page.content()


def test_llm_unavailable_shows_clear_message(page: Page):
    unreachable = Settings()
    unreachable.ollama_base_url = "http://127.0.0.1:1"  # nothing listens here: simulates Ollama stopped
    srv = _serve(create_default_app(unreachable))
    try:
        page.goto(f"http://127.0.0.1:{srv.server_port}")
        page.fill("#text-input", WORKED_EXAMPLE)
        page.click("button[type=submit]")

        expect(page.locator("#error")).to_contain_text("language model isn't available")
        expect(page.locator("#loading")).to_be_hidden()
        expect(page.locator("#parse-form button")).to_be_enabled()
    finally:
        srv.shutdown()


def test_identical_resubmit_makes_no_second_llm_call(page: Page, url, counting_pipeline):
    page.goto(url)
    page.fill("#text-input", WORKED_EXAMPLE)
    page.click("button[type=submit]")
    expect(page.locator("#download")).to_be_visible(timeout=LLM_TIMEOUT)
    calls = counting_pipeline.text_calls

    page.click("button[type=submit]")
    expect(page.locator("#download")).to_be_visible()

    assert counting_pipeline.text_calls == calls
