import pytest

from flowchartmaker.config import Settings
from flowchartmaker.llm.provider import LLMConfigurationError, LLMProvider


def _settings(**overrides) -> Settings:
    settings = Settings()
    settings.llm_provider = overrides.get("llm_provider", "ollama")
    settings.ollama_base_url = overrides.get("ollama_base_url", "http://localhost:11434")
    settings.ollama_model = overrides.get("ollama_model", "llama3.2")
    settings.gemini_api_key = overrides.get("gemini_api_key")
    settings.gemini_model = overrides.get("gemini_model", "gemini-1.5-flash")
    return settings


def test_valid_ollama_config_constructs_successfully():
    provider = LLMProvider(_settings())
    assert provider.chat_model is not None


def test_unreachable_ollama_url_raises_configuration_error():
    with pytest.raises(LLMConfigurationError):
        LLMProvider(_settings(ollama_base_url="http://localhost:59999"))


def test_missing_gemini_api_key_raises_configuration_error():
    with pytest.raises(LLMConfigurationError):
        LLMProvider(_settings(llm_provider="gemini", gemini_api_key=None))


def test_unknown_provider_raises_configuration_error():
    with pytest.raises(LLMConfigurationError):
        LLMProvider(_settings(llm_provider="not-a-real-provider"))
