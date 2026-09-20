from flask import Flask

from flowchartmaker.rendering.mermaid_renderer import MermaidRenderer
from flowchartmaker.web.routes import DiagramStore, register_routes


def create_app(pipeline) -> Flask:
    """Flask app factory. `pipeline` is any object with parse_text/parse_image -> ParseResult."""
    app = Flask(__name__)
    register_routes(app, pipeline, MermaidRenderer(), DiagramStore())
    return app
