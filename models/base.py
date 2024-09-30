# models/base.py
from pydantic import BaseModel, Field
import uuid


class BaseModelWithID(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
