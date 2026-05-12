"""Shared LangGraph state shape for the HR-RAG agent."""

from __future__ import annotations

from typing import Annotated, Any, Literal, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


def _dedup_sources(
    left: list[dict[str, Any]], right: list[dict[str, Any]] | None
) -> list[dict[str, Any]]:
    if not right:
        return list(left)
    seen = {s.get("source_uri") for s in left}
    merged = list(left)
    for src in right:
        if src.get("source_uri") in seen:
            continue
        seen.add(src.get("source_uri"))
        merged.append(src)
    return merged


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    # Authenticated principal. Set once per request by the API layer and
    # injected into tool calls so the LLM cannot choose another user's id.
    employee_id: str
    retrieved_chunks: list[dict[str, Any]]
    retrieval_attempts: int
    last_query: str
    retrieval_origin: Literal["initial", "agent", "retry"] | None
    grade_verdict: Literal["sufficient", "insufficient", "ambiguous"] | None
    clarification_question: str | None
    cited_sources: Annotated[list[dict[str, Any]], _dedup_sources]
