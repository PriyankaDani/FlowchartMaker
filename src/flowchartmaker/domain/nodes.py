from typing import Literal

from pydantic import BaseModel


class Node(BaseModel):
    id: str
    label: str


class StartNode(Node):
    type: Literal["start"]


class EndNode(Node):
    type: Literal["end"]


class Step(Node):
    type: Literal["step"]


class Decision(Node):
    type: Literal["decision"]
