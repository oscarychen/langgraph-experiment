from fastapi import APIRouter

from hr_rag.schemas.chat import ChatRequest, ChatResponse

router = APIRouter()


@router.post("/", response_model=ChatResponse)
async def chat(request: ChatRequest):
    # TODO: Wire up LangGraph RAG pipeline
    return ChatResponse(
        answer="RAG pipeline not yet implemented.",
        sources=[],
    )
