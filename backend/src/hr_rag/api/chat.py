from datetime import date

from fastapi import APIRouter, Depends
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage

from hr_rag.auth import get_current_employee_id
from hr_rag.rag.graph import agent_graph
from hr_rag.rag.prompts import HR_SYSTEM_PROMPT
from hr_rag.schemas.chat import ChatRequest, ChatResponse, SourceRef

router = APIRouter()


def _message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "".join(parts)


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    employee_id: str = Depends(get_current_employee_id),
) -> ChatResponse:
    system_prompt = HR_SYSTEM_PROMPT.format(
        employee_id=employee_id,
        today=date.today().isoformat(),
    )
    initial_state = {
        "messages": [
            SystemMessage(content=system_prompt),
            HumanMessage(content=request.question),
        ]
    }
    result = await agent_graph.ainvoke(initial_state)
    sources = [SourceRef(**ref) for ref in result.get("cited_sources") or []]
    return ChatResponse(
        answer=_message_text(result["messages"][-1]),
        sources=sources,
    )
