from pydantic import BaseModel

from flowchartmaker.domain.flowchart import Flowchart


class ParseTrace(BaseModel):
    sketch_description: str | None = None


class ParseResult(BaseModel):
    flowchart: Flowchart
    trace: ParseTrace
