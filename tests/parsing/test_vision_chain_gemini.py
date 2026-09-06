"""VisionParsingChain exercised against Gemini (gemini-2.5-flash).

Per docs/adr/0005-vision-chain-tested-against-gemini-not-ollama.md, this is the documented
Ollama-equivalent for this component: no vision-capable Ollama model available locally proved
reliable/loadable on this hardware. These tests require a GEMINI_API_KEY.

Gemini's free tier is rate-limited (5 req/min, 250k tokens/min, 20 req/day at time of writing).
This file makes exactly one LLM call per test (3 total) -- do not add more calls here without
re-checking the daily budget in docs/adr/0005-vision-chain-tested-against-gemini-not-ollama.md.
"""

from pathlib import Path

import pytest

from flowchartmaker.config import Settings
from flowchartmaker.domain.errors import SketchUnreadableError
from flowchartmaker.llm.provider import LLMProvider
from flowchartmaker.parsing.vision_chain import VisionParsingChain

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

pytestmark = pytest.mark.skipif(
    not Settings().gemini_api_key,
    reason="GEMINI_API_KEY not set; skipping Gemini-backed vision chain tests.",
)


@pytest.fixture(scope="module")
def chain() -> VisionParsingChain:
    settings = Settings()
    settings.llm_provider = "gemini"
    return VisionParsingChain(LLMProvider(settings))


def _read_fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def test_clean_sketch_description_mentions_expected_shapes(chain: VisionParsingChain):
    description = chain.describe(_read_fixture("clean_sketch.png")).lower()

    assert "start" in description
    assert "end" in description
    assert "email" in description
    assert "urgent" in description
    assert "yes" in description
    assert "no" in description


def test_messy_scribble_raises_sketch_unreadable_error(chain: VisionParsingChain):
    with pytest.raises(SketchUnreadableError):
        chain.describe(_read_fixture("messy_scribble.png"))


def test_blank_page_raises_sketch_unreadable_error(chain: VisionParsingChain):
    with pytest.raises(SketchUnreadableError):
        chain.describe(_read_fixture("blank_page.png"))
