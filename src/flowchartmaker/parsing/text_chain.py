from flowchartmaker.domain.errors import EmptyInputError
from flowchartmaker.domain.flowchart import Flowchart
from flowchartmaker.domain.trace import ParseResult, ParseTrace
from flowchartmaker.llm.provider import LLMProvider
from flowchartmaker.parsing.prompts import build_prompt


class TextParsingChain:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._structured_llm = llm_provider.chat_model.with_structured_output(Flowchart)

    def parse(self, text: str) -> ParseResult:
        if not text.strip():
            raise EmptyInputError("Input text is empty.")

        prompt = build_prompt(text)
        flowchart = self._structured_llm.invoke(prompt)
        return ParseResult(flowchart=flowchart, trace=ParseTrace())
