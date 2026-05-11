"""LangGraph nodes and routers for the conditional retrieval pipeline."""

from __future__ import annotations

import logging
from typing import Any, Literal

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import RunnableLambda

from hr_rag.config import settings
from hr_rag.rag.grader import grade_retrieval
from hr_rag.rag.llm import get_llm
from hr_rag.rag.prompts import NO_CHUNKS_MESSAGE, RETRIEVED_CHUNKS_TEMPLATE
from hr_rag.rag.retriever import retrieve_chunks
from hr_rag.rag.tools import HR_TOOLS, SEARCH_TOOL_NAME, search_hr_documents

logger = logging.getLogger(__name__)

Origin = Literal["initial", "agent", "retry"]


def _format_chunks_for_prompt(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "(no chunks retrieved)"
    parts: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[{i}] {chunk.get('title', '?')} "
            f"({chunk.get('source_uri', '')}) — score "
            f"{chunk.get('similarity', 0.0):.2f}\n"
            f"{chunk.get('chunk_text', '')}"
        )
    return "\n\n".join(parts)


def _latest_human_question(messages: list[BaseMessage]) -> str:
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            content = msg.content
            if isinstance(content, str):
                return content
            return "".join(
                block if isinstance(block, str) else block.get("text", "")
                for block in content
            )
    return ""


def _find_search_tool_call(message: BaseMessage) -> dict[str, Any] | None:
    tool_calls = getattr(message, "tool_calls", None) or []
    for call in tool_calls:
        if call.get("name") == SEARCH_TOOL_NAME:
            return call
    return None


def _resolve_retrieve_input(
    state: dict[str, Any],
) -> tuple[str, str | None, Origin]:
    """Return (query, tool_call_id, origin) for this retrieve invocation."""
    messages: list[BaseMessage] = state.get("messages", [])
    last = messages[-1] if messages else None
    if isinstance(last, AIMessage):
        call = _find_search_tool_call(last)
        if call is not None:
            args = call.get("args") or {}
            query = args.get("query") or state.get("last_query") or ""
            return query, call.get("id"), "agent"
    if isinstance(last, HumanMessage):
        content = last.content if isinstance(last.content, str) else ""
        return content, None, "initial"
    return state.get("last_query", ""), None, "retry"


def _source_refs(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    refs: list[dict[str, Any]] = []
    for chunk in chunks:
        uri = chunk.get("source_uri")
        if not uri or uri in seen:
            continue
        seen.add(uri)
        refs.append(
            {
                "title": chunk.get("title") or "",
                "source_uri": uri,
                "doc_type": chunk.get("doc_type"),
            }
        )
    return refs


async def retrieve_node(state: dict[str, Any]) -> dict[str, Any]:
    attempts = int(state.get("retrieval_attempts") or 0) + 1
    query, tool_call_id, origin = _resolve_retrieve_input(state)
    if not query:
        # Nothing to search on; emit a placeholder so the graph keeps moving.
        logger.warning("retrieve_node invoked without a resolvable query")
        return {
            "retrieval_attempts": attempts,
            "retrieved_chunks": [],
            "last_query": "",
            "retrieval_origin": origin,
            "messages": [SystemMessage(content=NO_CHUNKS_MESSAGE.format(query=""))],
        }

    chunks = await retrieve_chunks(query, top_k=settings.retrieval_top_k)
    formatted = _format_chunks_for_prompt(chunks)

    new_message: BaseMessage
    if tool_call_id is not None:
        content = formatted if chunks else NO_CHUNKS_MESSAGE.format(query=query)
        new_message = ToolMessage(
            content=content,
            tool_call_id=tool_call_id,
            name=SEARCH_TOOL_NAME,
        )
    elif chunks:
        new_message = SystemMessage(
            content=RETRIEVED_CHUNKS_TEMPLATE.format(
                query=query, formatted_chunks=formatted
            )
        )
    else:
        new_message = SystemMessage(content=NO_CHUNKS_MESSAGE.format(query=query))

    return {
        "messages": [new_message],
        "retrieved_chunks": chunks,
        "retrieval_attempts": attempts,
        "last_query": query,
        "retrieval_origin": origin,
        "cited_sources": _source_refs(chunks),
    }


async def grade_node(state: dict[str, Any]) -> dict[str, Any]:
    question = _latest_human_question(state.get("messages", []))
    chunks = state.get("retrieved_chunks") or []
    verdict = await grade_retrieval(question, chunks)

    delta: dict[str, Any] = {
        "grade_verdict": verdict.verdict,
        "clarification_question": None,
    }
    if verdict.verdict == "insufficient" and verdict.refined_query:
        delta["last_query"] = verdict.refined_query
        # Mark next retrieve as a retry so origin is preserved across the loop.
        delta["retrieval_origin"] = "retry"
    if verdict.verdict == "ambiguous":
        delta["clarification_question"] = verdict.clarification_question or (
            "Could you clarify your question?"
        )
    return delta


def clarify_node(state: dict[str, Any]) -> dict[str, Any]:
    question = state.get("clarification_question") or (
        "Could you clarify your question?"
    )
    return {"messages": [AIMessage(content=question)]}


def _make_agent_node():
    llm = get_llm().bind_tools(HR_TOOLS + [search_hr_documents])
    return (
        RunnableLambda(lambda state: state["messages"])
        | llm
        | RunnableLambda(lambda msg: {"messages": [msg]})
    )


agent_node = _make_agent_node()


def route_after_agent(state: dict[str, Any]) -> Literal["retrieve", "tools", "end"]:
    messages = state.get("messages") or []
    if not messages:
        return "end"
    last = messages[-1]
    tool_calls = getattr(last, "tool_calls", None) or []
    if not tool_calls:
        return "end"
    # Prioritize retrieval when the agent emits a mixed batch — the signaling
    # tool needs its tool_call_id satisfied by retrieve_node, not ToolNode.
    for call in tool_calls:
        if call.get("name") == SEARCH_TOOL_NAME:
            return "retrieve"
    return "tools"


def route_after_grade(
    state: dict[str, Any],
) -> Literal["agent", "retrieve", "clarify"]:
    attempts = int(state.get("retrieval_attempts") or 0)
    verdict = state.get("grade_verdict")
    origin = state.get("retrieval_origin")

    if attempts >= settings.max_retrieval_attempts:
        return "agent"
    if verdict == "insufficient":
        return "retrieve"
    if verdict == "ambiguous" and origin == "initial":
        return "clarify"
    # ambiguous mid-conversation downgrades to sufficient: hand back to agent
    # so any open tool_call gets satisfied and the agent can ask its own
    # follow-up question.
    return "agent"
