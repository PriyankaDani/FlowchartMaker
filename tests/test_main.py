"""Launcher: startup validation, browser opening, and server run mode (ticket 009)."""
from unittest.mock import MagicMock

from flowchartmaker.config import Settings
from flowchartmaker.llm.provider import LLMConfigurationError
from flowchartmaker.main import Launcher


def _launcher(factory=None, **kw):
    return Launcher(
        settings=Settings(),
        pipeline_factory=factory or MagicMock(),
        serve=kw.get("serve", MagicMock()),
        open_browser=kw.get("open_browser", MagicMock()),
        env_path="C:/apps/flowchartmaker/.env",
    )


def test_config_error_at_startup_names_the_problem_and_the_env_file(capsys):
    serve, browser = MagicMock(), MagicMock()
    launcher = _launcher(MagicMock(side_effect=LLMConfigurationError("GEMINI_API_KEY is not set")), serve=serve, open_browser=browser)

    code = launcher.run()

    out = capsys.readouterr().err
    assert code == 1
    assert "GEMINI_API_KEY is not set" in out
    assert "C:/apps/flowchartmaker/.env" in out
    serve.assert_not_called()
    browser.assert_not_called()


def test_healthy_start_serves_without_reloader_or_debug_and_opens_browser():
    serve, browser = MagicMock(), MagicMock()

    code = _launcher(serve=serve, open_browser=browser).run()

    assert code == 0
    serve.assert_called_once()
    _, kwargs = serve.call_args
    assert "reloader" not in kwargs and "debug" not in kwargs
    (sock,) = kwargs["sockets"]  # pre-bound, so the browser can't beat the server to the port
    assert sock.getsockname()[0] == "127.0.0.1"
    browser.assert_called_once_with(f"http://127.0.0.1:{sock.getsockname()[1]}")


def test_pipeline_is_built_once_and_shared_with_the_app():
    factory = MagicMock()

    _launcher(factory).run()

    factory.assert_called_once()
