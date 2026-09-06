import base64

from langchain_core.messages import HumanMessage

from flowchartmaker.domain.errors import EmptyInputError, SketchUnreadableError
from flowchartmaker.llm.provider import LLMProvider
from flowchartmaker.parsing.prompts import build_vision_system_message

_UNREADABLE_PREFIX = "UNREADABLE:"


class VisionParsingChain:
    def __init__(self, llm_provider: LLMProvider) -> None:
        self._chat_model = llm_provider.vision_chat_model

    def describe(self, image: bytes) -> str:
        if not image:
            raise EmptyInputError("No image provided.")

        message = HumanMessage(
            content=[
                {"type": "text", "text": "Describe this flowchart sketch."},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{base64.b64encode(image).decode()}"
                    },
                },
            ]
        )
        response = self._chat_model.invoke([build_vision_system_message(), message])
        description = response.content.strip()

        if description.startswith(_UNREADABLE_PREFIX):
            reason = description[len(_UNREADABLE_PREFIX):].strip()
            raise SketchUnreadableError(reason or "Sketch could not be read.")

        return description
