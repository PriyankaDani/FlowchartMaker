from unittest.mock import MagicMock

import pytest

from flowchartmaker.domain.errors import EmptyInputError, SketchUnreadableError
from flowchartmaker.parsing.vision_chain import VisionParsingChain


def _fake_llm_provider(response_text: str | None = None):
    provider = MagicMock()
    response = MagicMock()
    response.content = response_text
    provider.vision_chat_model.invoke.return_value = response
    return provider


def test_no_image_raises_without_llm_call():
    provider = _fake_llm_provider()
    chain = VisionParsingChain(provider)

    with pytest.raises(EmptyInputError):
        chain.describe(b"")

    provider.vision_chat_model.invoke.assert_not_called()


def test_readable_sketch_returns_description_string():
    provider = _fake_llm_provider(
        "A stadium shape labeled 'Start' points to a box labeled 'Check email', which "
        "points to a diamond labeled 'Urgent?'..."
    )
    chain = VisionParsingChain(provider)

    description = chain.describe(b"fake-image-bytes")

    assert isinstance(description, str)
    assert "Check email" in description


def test_unreadable_response_raises_sketch_unreadable_error():
    provider = _fake_llm_provider("UNREADABLE: the image is blank.")
    chain = VisionParsingChain(provider)

    with pytest.raises(SketchUnreadableError) as exc_info:
        chain.describe(b"fake-image-bytes")

    assert "blank" in exc_info.value.reason


def test_unreadable_response_with_no_reason_still_raises_with_default_message():
    provider = _fake_llm_provider("UNREADABLE:")
    chain = VisionParsingChain(provider)

    with pytest.raises(SketchUnreadableError):
        chain.describe(b"fake-image-bytes")
