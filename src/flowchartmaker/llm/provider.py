import ollama
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_ollama import ChatOllama

from flowchartmaker.config import Settings


class LLMConfigurationError(Exception):
    """Raised when the configured LLM provider is missing config or unreachable."""


class LLMProvider:
    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._chat_model = self._build_chat_model()

    @property
    def chat_model(self) -> BaseChatModel:
        return self._chat_model

    def _build_chat_model(self) -> BaseChatModel:
        provider = self._settings.llm_provider
        if provider == "ollama":
            return self._build_ollama()
        if provider == "gemini":
            return self._build_gemini()
        raise LLMConfigurationError(
            f"Unknown LLM_PROVIDER {provider!r}. Expected 'ollama' or 'gemini'."
        )

    def _build_ollama(self) -> BaseChatModel:
        base_url = self._settings.ollama_base_url
        model_name = self._settings.ollama_model
        try:
            ollama.Client(host=base_url).list()
        except Exception as exc:
            raise LLMConfigurationError(
                f"Could not reach Ollama at {base_url!r}. Is Ollama running? ({exc})"
            ) from exc
        return ChatOllama(base_url=base_url, model=model_name, temperature=0)

    def _build_gemini(self) -> BaseChatModel:
        if not self._settings.gemini_api_key:
            raise LLMConfigurationError(
                "GEMINI_API_KEY is not set; required when LLM_PROVIDER=gemini."
            )
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=self._settings.gemini_model,
            google_api_key=self._settings.gemini_api_key,
        )
