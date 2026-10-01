from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    type: str = Field(min_length=2, max_length=64)
    content: str = Field(min_length=1)
    confidence: float = Field(default=0.5, ge=0, le=1)
    importance: float = Field(default=0.5, ge=0, le=1)
    source: str = Field(default="EXTRACTED", min_length=2, max_length=64)
    provenance_json: dict = Field(default_factory=dict)


class MemoryUpdate(BaseModel):
    content: str | None = Field(default=None, min_length=1)
    confidence: float | None = Field(default=None, ge=0, le=1)
    importance: float | None = Field(default=None, ge=0, le=1)
    status: Literal["ACTIVE", "SUPERSEDED", "REJECTED", "PENDING_REVIEW"] | None = None
    provenance_json: dict | None = None
    reviewed_by: str | None = Field(default=None, min_length=2, max_length=64)
    decision: str | None = Field(default=None, min_length=2, max_length=64)
    decision_reason: str | None = Field(default=None, min_length=2, max_length=255)


class MemoryOut(BaseModel):
    id: int
    user_id: str
    type: str
    content: str
    confidence: float
    importance: float
    status: str
    source: str
    provenance_json: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemoryReviewRequest(BaseModel):
    decision: str = Field(pattern="^(approve|reject)$")
    reason: str = Field(min_length=3, max_length=255)
