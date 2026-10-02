from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    notes: str = ""
    due_at: datetime
    recurrence_rule: str | None = Field(default=None, max_length=128)


class ReminderUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    notes: str | None = None
    due_at: datetime | None = None
    recurrence_rule: str | None = Field(default=None, max_length=128)
    status: Literal["ACTIVE", "COMPLETED", "CANCELLED"] | None = None


class ReminderOut(BaseModel):
    id: int
    user_id: str
    title: str
    notes: str
    due_at: datetime
    recurrence_rule: str | None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
