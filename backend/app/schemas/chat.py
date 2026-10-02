from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    conversation_id: int | None = None
    extraction_mode: Literal["auto", "off"] | None = None


class ChatAction(BaseModel):
    action: str
    status: Literal["executed", "ignored", "invalid"]
    rule_id: str
    reminder_id: int | None = None


class MemoryContextItem(BaseModel):
    id: int
    type: str
    content: str
    importance: float


class ChatResponse(BaseModel):
    conversation_id: int
    reply: str
    actions: list[ChatAction] = Field(default_factory=list)
    memory_context: list[MemoryContextItem] | None = None
