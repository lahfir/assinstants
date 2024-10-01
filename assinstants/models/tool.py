# models/tool.py
from pydantic import BaseModel
from .function import FunctionDefinition


class FunctionTool(BaseModel):
    type: str = "function"
    function: FunctionDefinition


class Tool(BaseModel):
    tool: FunctionTool
