from pydantic import BaseModel


class Branch(BaseModel):
    source_id: str
    target_id: str
    label: str | None = None
