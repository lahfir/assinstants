# models/thread.py
from .base import BaseModelWithID
from typing import List
from .message import Message
from .assistant import Assistant
from pydantic import Field


class Thread(BaseModelWithID):
    messages: List[Message] = Field(default_factory=list)
    assistants: List[Assistant] = Field(default_factory=list)
