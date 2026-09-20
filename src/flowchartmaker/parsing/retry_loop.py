from collections.abc import Callable

from flowchartmaker.domain.errors import FlowchartValidationError
from flowchartmaker.domain.trace import ParseResult


class RetryingParser:
    """Retries a parse-once callable on FlowchartValidationError, feeding back the failures.

    Each retry is a fresh, stateless prompt (no accumulated history). After `max_retries`
    retries the last FlowchartValidationError is re-raised unchanged. Any other exception
    (e.g. SketchUnreadableError) propagates immediately.
    """

    def __init__(self, parse_fn: Callable[[str], ParseResult], max_retries: int = 2) -> None:
        self._parse_fn = parse_fn
        self._max_retries = max_retries

    def parse(self, text: str) -> ParseResult:
        prompt = text
        for attempt in range(self._max_retries + 1):
            try:
                return self._parse_fn(prompt)
            except FlowchartValidationError as error:
                if attempt == self._max_retries:
                    raise
                prompt = self._build_retry_prompt(text, error)
        raise AssertionError("unreachable")  # pragma: no cover

    @staticmethod
    def _build_retry_prompt(original_text: str, error: FlowchartValidationError) -> str:
        previous = error.raw_output if error.raw_output is not None else "(not available)"
        return (
            f"{original_text}\n\n"
            "Your previous attempt was invalid.\n"
            f"Previous output:\n{previous}\n\n"
            f"Validation problems:\n{error.to_llm_feedback()}\n\n"
            "Produce a corrected flowchart that fixes these problems."
        )
