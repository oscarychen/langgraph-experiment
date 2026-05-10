from datetime import date

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage, SystemMessage

from hr_rag.auth import get_current_employee_id
from hr_rag.rag.graph import agent_graph
from hr_rag.rag.prompts import HR_SYSTEM_PROMPT
from hr_rag.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


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
    return ChatResponse(answer=result["messages"][-1].content, sources=[])
