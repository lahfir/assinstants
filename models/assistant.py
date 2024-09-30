# models/assistant.py
from .base import BaseModelWithID
from .tool import Tool
from typing import Dict, Any, Callable, List, Optional
from pydantic import Field


class Assistant(BaseModelWithID):
    name: str
    instructions: str
    model: str
    custom_llm_function: Callable
    provider_config: Dict[str, Any] = Field(
        default_factory=dict, description="Provider configuration"
    )
    tools: List[Tool] = Field(
        default_factory=list, description="List of tools available to the assistant"
    )

    def __init__(self, *args, tools: Optional[List[Tool]] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tools: List[Tool] = tools or []
