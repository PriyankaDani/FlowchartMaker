import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def resource_path(relative: str, *, writable: bool = False) -> Path:
    """Resolve `relative` identically in dev and frozen (PyInstaller) mode.

    Bundled read-only assets (`writable=False`) live under `sys._MEIPASS` when frozen, and under
    `src/` in dev, so the same package-relative path ("flowchartmaker/web/templates") works in both.
    User-editable files such as `.env` (`writable=True`) live next to the executable when frozen
    (the bundle dir is a temp dir), and at the repo root in dev.
    """
    frozen = getattr(sys, "frozen", False)
    if writable:
        base = Path(sys.executable).parent if frozen else Path(__file__).resolve().parents[2]
    else:
        base = Path(sys._MEIPASS) if frozen else Path(__file__).resolve().parents[1]
    return base / relative


load_dotenv(resource_path(".env", writable=True))


class Settings:
    def __init__(self) -> None:
        self.llm_provider = os.getenv("LLM_PROVIDER", "ollama")
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
        self.ollama_vision_model = os.getenv("OLLAMA_VISION_MODEL", "llava")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
