from datetime import datetime

from pydantic import BaseModel


class RoutineCandidateOut(BaseModel):
    id: int
    user_id: str
    description: str
    confidence: float
    status: str
    observation_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RoutineSuggestionOut(BaseModel):
    title: str
    description: str
    confidence: float
    source_memory_ids: list[int]
    source_reminder_ids: list[int]


class NextActionOut(BaseModel):
    priority: int
    title: str
    description: str
    source_reminder_id: int | None
    source_memory_id: int | None
