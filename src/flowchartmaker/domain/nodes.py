from typing import Literal

from pydantic import BaseModel


class Node(BaseModel):
    id: str
    label: str


class StartNode(Node):
    type: Literal["start"] = "start"


class EndNode(Node):
    type: Literal["end"] = "end"


class Step(Node):
    type: Literal["step"] = "step"


class Decision(Node):
    type: Literal["decision"] = "decision"
