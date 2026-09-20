import socket
import sys
import webbrowser
from collections.abc import Callable
from pathlib import Path

import waitress

from flowchartmaker.config import Settings, resource_path
from flowchartmaker.llm.provider import LLMConfigurationError
from flowchartmaker.parsing.pipeline import ParsingPipeline
from flowchartmaker.web.app import build_pipeline, create_app

HOST = "127.0.0.1"


class Launcher:
    """Entry point for the packaged app: validates config, serves Flask via waitress, opens the browser.

    Config is validated *before* the UI is usable (unlike the lazy path used in tests), so a missing
    key or an unreachable Ollama is reported on the console with the `.env` location to fix.
    Waitress (no reloader, no debug) is used because the reloader re-execs a script that doesn't
    exist in a frozen build.
    """

    def __init__(
        self,
        settings: Settings | None = None,
        pipeline_factory: Callable[[Settings | None], ParsingPipeline] | None = None,
        serve: Callable = waitress.serve,
        open_browser: Callable[[str], object] = webbrowser.open,
        env_path: str | Path | None = None,
    ) -> None:
        self._settings = settings or Settings()
        self._pipeline_factory = pipeline_factory or build_pipeline
        self._serve = serve
        self._open_browser = open_browser
        self._env_path = env_path or resource_path(".env", writable=True)

    def run(self) -> int:
        try:
            pipeline = self._pipeline_factory(self._settings)
        except LLMConfigurationError as exc:
            print(
                f"FlowchartMaker can't start: {exc}\n"
                f"Fix it in {self._env_path} (see .env.example) and start the app again.",
                file=sys.stderr,
            )
            return 1

        sock = socket.socket()
        sock.bind((HOST, 0))
        sock.listen()
        url = f"http://{HOST}:{sock.getsockname()[1]}"
        print(f"FlowchartMaker running at {url} (close this window to stop)")
        self._open_browser(url)
        self._serve(create_app(pipeline), sockets=[sock])
        return 0


def main() -> None:
    sys.exit(Launcher().run())


if __name__ == "__main__":
    main()
