import hashlib

import httpx
from flask import Flask, Response, jsonify, render_template, request

from flowchartmaker.domain.errors import (
    EmptyInputError,
    FlowchartValidationError,
    SketchUnreadableError,
)
from flowchartmaker.llm.provider import LLMConfigurationError

EMPTY_INPUT_MESSAGE = "Please enter a process description or upload a sketch."
SKETCH_UNREADABLE_MESSAGE = (
    "We couldn't confidently read this sketch. Try a clearer, higher-contrast photo "
    "or describe the process in text instead."
)
VALIDATION_MESSAGE = (
    "We couldn't turn that into a valid flowchart. Try rephrasing the process with "
    "clearer steps and outcomes."
)
LLM_UNAVAILABLE_MESSAGE = (
    "The language model isn't available right now. Check that Ollama is running "
    "(or that your Gemini API key is set in .env), then try again."
)
UNEXPECTED_MESSAGE = "Something went wrong on our side. Please try again."

_LLM_UNAVAILABLE_ERRORS = (LLMConfigurationError, ConnectionError, httpx.TransportError)


class DiagramStore:
    """Holds the SVG of the current diagram. The app is single-user and local, so one slot suffices."""

    def __init__(self) -> None:
        self.svg: str | None = None
        self._mermaid_by_input: dict[str, str] = {}

    def cached_mermaid(self, key: str) -> str | None:
        return self._mermaid_by_input.get(key)

    def cache_mermaid(self, key: str, mermaid: str) -> None:
        # Only the latest input is remembered: enough to make an accidental re-submit free.
        self._mermaid_by_input = {key: mermaid}


def register_routes(app: Flask, pipeline, renderer, store: DiagramStore) -> None:
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/parse")
    def parse():
        store.svg = None
        try:
            image = request.files.get("image")
            if image is not None and image.filename:
                data = image.read()
                key = "image:" + hashlib.sha256(data).hexdigest()
                cached = store.cached_mermaid(key)
                if cached is not None:
                    return jsonify(mermaid=cached)
                result = pipeline.parse_image(data)
            else:
                text = request.form.get("text", "")
                key = "text:" + text
                cached = store.cached_mermaid(key)
                if cached is not None:
                    return jsonify(mermaid=cached)
                result = pipeline.parse_text(text)
        except EmptyInputError:
            return jsonify(error=EMPTY_INPUT_MESSAGE), 400
        except SketchUnreadableError:
            return jsonify(error=SKETCH_UNREADABLE_MESSAGE), 422
        except FlowchartValidationError:
            return jsonify(error=VALIDATION_MESSAGE), 422
        except _LLM_UNAVAILABLE_ERRORS:
            return jsonify(error=LLM_UNAVAILABLE_MESSAGE), 503
        except Exception:
            app.logger.exception("Unexpected error in /parse")
            return jsonify(error=UNEXPECTED_MESSAGE), 500
        mermaid = renderer.render(result.flowchart)
        store.cache_mermaid(key, mermaid)
        return jsonify(mermaid=mermaid)

    @app.post("/svg")
    def upload_svg():
        svg = request.get_data(as_text=True)
        if not svg.lstrip().startswith(("<svg", "<?xml")) or "<svg" not in svg:
            return jsonify(error="That doesn't look like an SVG."), 400
        store.svg = svg
        return "", 204

    @app.get("/download-svg")
    def download_svg():
        if store.svg is None:
            return jsonify(error="There's nothing to download yet — generate a flowchart first."), 404
        return Response(
            store.svg,
            mimetype="image/svg+xml",
            headers={"Content-Disposition": 'attachment; filename="flowchart.svg"'},
        )
