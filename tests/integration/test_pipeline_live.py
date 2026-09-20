"""ParsingPipeline end-to-end (ticket 006 exit conditions).

Text stage runs on local Ollama; the vision stage runs on Gemini per
docs/adr/0005-vision-chain-tested-against-gemini-not-ollama.md (needs GEMINI_API_KEY).
Budget: 2 Gemini vision calls per run (free tier is 20/day) -- run sparingly.
"""
from pathlib import Path

import pytest

from flowchartmaker.config import Settings
from flowchartmaker.domain.errors import SketchUnreadableError
from flowchartmaker.domain.nodes import Decision, EndNode, StartNode
from flowchartmaker.llm.provider import LLMProvider
from flowchartmaker.parsing.pipeline import ParsingPipeline
from flowchartmaker.parsing.text_chain import TextParsingChain
from flowchartmaker.parsing.vision_chain import VisionParsingChain

FIXTURES = Path(__file__).resolve().parents[1] / "parsing" / "fixtures"
WORKED_EXAMPLE = "Check email. If it's urgent, reply now. Otherwise, add it to the queue."

pytestmark = pytest.mark.skipif(
    not Settings().gemini_api_key, reason="GEMINI_API_KEY not set; vision stage needs Gemini."
)


@pytest.fixture(scope="module")
def pipeline() -> ParsingPipeline:
    gemini = Settings()
    gemini.llm_provider = "gemini"
    return ParsingPipeline(TextParsingChain(LLMProvider()), VisionParsingChain(LLMProvider(gemini)))


def _shape(flowchart):
    return (
        sum(isinstance(n, StartNode) for n in flowchart.nodes),
        sum(isinstance(n, EndNode) for n in flowchart.nodes),
        sum(isinstance(n, Decision) for n in flowchart.nodes),
        {e.label for e in flowchart.edges if e.label},
    )


def test_clean_sketch_converges_with_equivalent_text(pipeline: ParsingPipeline):
    image_result = pipeline.parse_image((FIXTURES / "clean_sketch.png").read_bytes())
    text_result = pipeline.parse_text(WORKED_EXAMPLE)

    assert _shape(image_result.flowchart) == _shape(text_result.flowchart)
    assert image_result.trace.sketch_description
    assert text_result.trace.sketch_description is None


def test_messy_sketch_raises_sketch_unreadable(pipeline: ParsingPipeline):
    with pytest.raises(SketchUnreadableError):
        pipeline.parse_image((FIXTURES / "messy_scribble.png").read_bytes())

