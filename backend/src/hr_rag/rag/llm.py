from functools import lru_cache

# For prod use: langchain_google_vertexai.ChatVertexAI
from langchain_google_genai import ChatGoogleGenerativeAI

from hr_rag.config import settings


@lru_cache(maxsize=1)
def get_llm() -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=settings.gemini_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    )
