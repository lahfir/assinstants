# models/message.py
from typing import Literal, Optional, Union
from pydantic import BaseModel
from datetime import datetime


class Message(BaseModel):
    role: Union[Literal["user"], Literal["assistant"]]
    content: str
    assistant_id: Optional[str] = None
    created_at: Optional[datetime] = None
