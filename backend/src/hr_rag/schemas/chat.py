from typing import Literal

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    question: str
    history: list[ChatMessage] = []
    session_id: str | None = None


class SourceRef(BaseModel):
    title: str
    source_uri: str
    doc_type: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
