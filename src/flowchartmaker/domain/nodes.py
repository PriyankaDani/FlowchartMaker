from pydantic import BaseModel


class Node(BaseModel):
    id: str
    label: str


class StartNode(Node):
    pass


class EndNode(Node):
    pass


class Step(Node):
    pass


class Decision(Node):
    pass
