from flowchartmaker.domain.errors import EmptyInputError
from flowchartmaker.domain.trace import ParseResult
from flowchartmaker.parsing.retry_loop import RetryingParser
from flowchartmaker.parsing.text_chain import TextParsingChain
from flowchartmaker.parsing.vision_chain import VisionParsingChain


class ParsingPipeline:
    """Single entry point for the UI. Image input funnels through the vision chain's
    Sketch description into the same text chain used for typed input (ADR 0001).

    The text stage is wrapped in RetryingParser (ticket 011) for both paths. Errors propagate
    unchanged (after retries are exhausted, for FlowchartValidationError); no conversion
    happens at the seam.
    """

    def __init__(self, text_chain: TextParsingChain, vision_chain: VisionParsingChain) -> None:
        self._text_parser = RetryingParser(text_chain.parse)
        self._vision_chain = vision_chain

    def parse_text(self, text: str) -> ParseResult:
        return self._text_parser.parse(text)

    def parse_image(self, image: bytes) -> ParseResult:
        if not image:
            raise EmptyInputError("No image provided.")

        description = self._vision_chain.describe(image)
        result = self._text_parser.parse(description)
        result.trace.sketch_description = description
        return result
