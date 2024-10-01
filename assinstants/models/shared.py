# models/shared.py
from pydantic import BaseModel
from typing import Dict, Any, Optional, List


class FunctionCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class StepDetails(BaseModel):
    step_number: int
    description: str
    function_calls: Optional[List[FunctionCall]] = None
    results: Optional[Any] = None
