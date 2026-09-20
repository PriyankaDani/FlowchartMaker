from flask import Flask, Response, jsonify, render_template, request

from flowchartmaker.domain.errors import (
    EmptyInputError,
    FlowchartValidationError,
    SketchUnreadableError,
)

EMPTY_INPUT_MESSAGE = "Please enter a process description or upload a sketch."
SKETCH_UNREADABLE_MESSAGE = (
    "We couldn't confidently read this sketch. Try a clearer, higher-contrast photo "
    "or describe the process in text instead."
)
VALIDATION_MESSAGE = (
    "We couldn't turn that into a valid flowchart. Try rephrasing the process with "
    "clearer steps and outcomes."
)


class DiagramStore:
    """Holds the SVG of the current diagram. The app is single-user and local, so one slot suffices."""

    def __init__(self) -> None:
        self.svg: str | None = None


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
                result = pipeline.parse_image(image.read())
            else:
                result = pipeline.parse_text(request.form.get("text", ""))
        except EmptyInputError:
            return jsonify(error=EMPTY_INPUT_MESSAGE), 400
        except SketchUnreadableError:
            return jsonify(error=SKETCH_UNREADABLE_MESSAGE), 422
        except FlowchartValidationError:
            return jsonify(error=VALIDATION_MESSAGE), 422
        return jsonify(mermaid=renderer.render(result.flowchart))

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
