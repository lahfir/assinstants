# models/run.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
import uuid
from datetime import datetime
from enum import Enum
from .shared import StepDetails


class RunStatus(str, Enum):
    QUEUED = "queued"
    IN_PROGRESS = "in_progress"
    REQUIRES_ACTION = "requires_action"
    COMPLETED = "completed"
    FAILED = "failed"


class RequiredAction(BaseModel):
    type: str
    description: str
    data: Optional[Dict[str, Any]] = None


class Run(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assistant_id: str
    thread_id: str
    status: RunStatus = RunStatus.QUEUED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: List[StepDetails] = Field(default_factory=list)
    error: Optional[str] = None
    token_usage: Dict[str, int] = Field(default_factory=dict)
    required_action: Optional[RequiredAction] = None
