from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None


class SourceRef(BaseModel):
    title: str
    source_uri: str
    doc_type: str | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceRef]
