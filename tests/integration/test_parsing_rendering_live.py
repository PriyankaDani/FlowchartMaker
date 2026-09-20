"""ParsingPipeline -> MermaidRenderer with real LLM-produced Flowcharts (ticket 007).

Text stage runs on local Ollama. The image test also needs Gemini for the vision stage
(ADR 0005): 1 call per run, so run sparingly.
"""
import re
from pathlib import Path

import pytest

from flowchartmaker.config import Settings
from flowchartmaker.domain.nodes import Decision
from flowchartmaker.llm.provider import LLMProvider
from flowchartmaker.parsing.pipeline import ParsingPipeline
from flowchartmaker.parsing.text_chain import TextParsingChain
from flowchartmaker.parsing.vision_chain import VisionParsingChain
from flowchartmaker.rendering.mermaid_renderer import MermaidRenderer

FIXTURES = Path(__file__).resolve().parents[1] / "parsing" / "fixtures"
WORKED_EXAMPLE = "Check email. If it's urgent, reply now. Otherwise, add it to the queue."

NODE_DEF = re.compile(r"^\s+(?P<id>\w+)(?P<open>\(\[|\[|\{)(?P<label>.*?)(?:\]\)|\]|\})$")
EDGE = re.compile(r"^\s+(?P<src>\w+) -->(?:\|(?P<label>.*?)\|)? (?P<dst>\w+)$")


def _assert_valid_mermaid(out: str) -> tuple[dict[str, str], list[tuple[str, str | None, str]]]:
    lines = out.splitlines()
    assert lines[0] == "flowchart TD"
    defs, edges = {}, []
    for line in lines[1:]:
        if m := NODE_DEF.match(line):
            assert m["id"] not in defs, f"duplicate node id {m['id']}"
            assert m["id"].lower() not in MermaidRenderer.RESERVED
            defs[m["id"]] = m["open"]
        elif m := EDGE.match(line):
            edges.append((m["src"], m["label"], m["dst"]))
        else:
            pytest.fail(f"unrecognised Mermaid line: {line!r}")
    for src, _, dst in edges:
        assert src in defs and dst in defs
    return defs, edges


def _summary(defs, edges):
    return (
        sum(o == "([" for o in defs.values()),
        sum(o == "{" for o in defs.values()),
        sorted(label for _, label, _ in edges if label),
    )


@pytest.fixture(scope="module")
def text_pipeline() -> ParsingPipeline:
    return ParsingPipeline(TextParsingChain(LLMProvider()), vision_chain=None)


@pytest.fixture(scope="module")
def renderer() -> MermaidRenderer:
    return MermaidRenderer()


def test_worked_example_text_renders_expected_structure(text_pipeline, renderer):
    out = renderer.render(text_pipeline.parse_text(WORKED_EXAMPLE).flowchart)
    defs, edges = _assert_valid_mermaid(out)

    assert _summary(defs, edges) == (2, 1, ["No", "Yes"])


@pytest.mark.skipif(not Settings().gemini_api_key, reason="GEMINI_API_KEY not set.")
def test_worked_example_image_renders_equivalent_to_text(text_pipeline, renderer):
    gemini = Settings()
    gemini.llm_provider = "gemini"
    pipeline = ParsingPipeline(TextParsingChain(LLMProvider()), VisionParsingChain(LLMProvider(gemini)))

    image_out = renderer.render(pipeline.parse_image((FIXTURES / "clean_sketch.png").read_bytes()).flowchart)
    text_out = renderer.render(text_pipeline.parse_text(WORKED_EXAMPLE).flowchart)

    assert _summary(*_assert_valid_mermaid(image_out)) == _summary(*_assert_valid_mermaid(text_out))


def test_retry_loop_process_renders(text_pipeline, renderer):
    flowchart = text_pipeline.parse_text(
        "Submit the report. A reviewer checks it. If it needs changes, go back and "
        "revise it, then submit again. If it is approved, publish it."
    ).flowchart
    _, edges = _assert_valid_mermaid(renderer.render(flowchart))

    assert any(isinstance(n, Decision) for n in flowchart.nodes)
    assert len(edges) == len(flowchart.edges)


def test_reserved_word_node_id_is_sanitized(text_pipeline, renderer):
    # The LLM ignores requested ids but sometimes picks a reserved one (e.g. "end") on its own,
    # so sample a few runs. Deterministic collision handling is covered in test_mermaid_renderer.py.
    for _ in range(4):
        flowchart = text_pipeline.parse_text(
            "Pack the box, then ship it. Give the node ids \"graph\" and \"subgraph\" to the two steps."
        ).flowchart
        if any(n.id.lower() in MermaidRenderer.RESERVED for n in flowchart.nodes):
            _assert_valid_mermaid(renderer.render(flowchart))
            return
    pytest.skip("LLM never assigned a reserved-word id in 4 runs; nothing to sanitize.")


@pytest.mark.parametrize(
    "description",
    [
        "Wash the dishes.",
        "Wake up, brush teeth, eat breakfast, leave for work.",
        "A customer places an order. If the item is in stock, ship it; otherwise back-order it and email the customer.",
        "Receive a support ticket. If it is a bug, file it with engineering; if it is a question, answer it; "
        "if it is a feature request, add it to the backlog. Then close the ticket.",
        "Try to log in. If the password is wrong, try again, up to three times. After three failures, "
        "lock the account. If the login works, show the dashboard.",
        "Cook pasta: boil water, add pasta, wait ten minutes, drain. If it is too firm, boil another two minutes.",
    ],
)
def test_varied_descriptions_round_trip(text_pipeline, renderer, description):
    flowchart = text_pipeline.parse_text(description).flowchart

    defs, edges = _assert_valid_mermaid(renderer.render(flowchart))

    assert len(defs) == len(flowchart.nodes)
    assert len(edges) == len(flowchart.edges)
