from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: int | None = None
    extraction_mode: Literal["auto", "off"] | None = None


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
