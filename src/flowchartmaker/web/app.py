from collections.abc import Callable

from flask import Flask

from flowchartmaker.config import Settings
from flowchartmaker.domain.trace import ParseResult
from flowchartmaker.llm.provider import LLMProvider
from flowchartmaker.parsing.pipeline import ParsingPipeline
from flowchartmaker.parsing.text_chain import TextParsingChain
from flowchartmaker.parsing.vision_chain import VisionParsingChain
from flowchartmaker.rendering.mermaid_renderer import MermaidRenderer
from flowchartmaker.web.routes import DiagramStore, register_routes


class LazyPipeline:
    """Builds the real pipeline on first use, so a missing Ollama / Gemini key surfaces as a
    user-facing message on the first request instead of crashing the app at startup.
    A failed build isn't remembered: fixing the config (e.g. starting Ollama) then just works."""

    def __init__(self, factory: Callable[[], ParsingPipeline]) -> None:
        self._factory = factory
        self._pipeline: ParsingPipeline | None = None

    def _get(self) -> ParsingPipeline:
        if self._pipeline is None:
            self._pipeline = self._factory()
        return self._pipeline

    def parse_text(self, text: str) -> ParseResult:
        return self._get().parse_text(text)

    def parse_image(self, image: bytes) -> ParseResult:
        return self._get().parse_image(image)


def build_pipeline(settings: Settings | None = None) -> ParsingPipeline:
    provider = LLMProvider(settings)
    return ParsingPipeline(TextParsingChain(provider), VisionParsingChain(provider))


def create_app(pipeline) -> Flask:
    """Flask app factory. `pipeline` is any object with parse_text/parse_image -> ParseResult."""
    app = Flask(__name__)
    register_routes(app, pipeline, MermaidRenderer(), DiagramStore())
    return app


def create_default_app(settings: Settings | None = None) -> Flask:
    """App wired to the real ParsingPipeline, configured from `settings` (default: .env)."""
    return create_app(LazyPipeline(lambda: build_pipeline(settings)))
