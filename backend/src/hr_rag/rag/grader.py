"""LLM judge that evaluates retrieved chunks against the user's question."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Literal

from langchain_core.runnables import Runnable
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from hr_rag.config import settings
from hr_rag.rag.prompts import GRADER_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)

Verdict = Literal["sufficient", "insufficient", "ambiguous"]


class GradeVerdict(BaseModel):
    verdict: Verdict
    refined_query: str | None = Field(
        default=None,
        description="Standalone search query, required when verdict is 'insufficient'.",
    )
    clarification_question: str | None = Field(
        default=None,
        description="Question to ask the user, required when verdict is 'ambiguous'.",
    )
    reasoning: str = Field(default="", description="One-sentence rationale.")


def _format_chunks_for_grader(chunks: list[dict[str, Any]]) -> str:
    if not chunks:
        return "(no chunks retrieved)"
    lines: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        lines.append(
            f"[{i}] {chunk.get('title', '?')} "
            f"(score {chunk.get('similarity', 0.0):.2f})\n"
            f"{chunk.get('chunk_text', '')}"
        )
    return "\n\n".join(lines)


async def grade_retrieval(question: str, chunks: list[dict[str, Any]]) -> GradeVerdict:
    """Judge whether `chunks` are sufficient to answer `question`.

    Fails open: on malformed LLM output, returns a 'sufficient' verdict so
    the user-facing flow keeps moving and the agent answers from whatever
    context is available.
    """
    prompt = GRADER_PROMPT_TEMPLATE.format(
        question=question,
        formatted_chunks=_format_chunks_for_grader(chunks),
    )
    llm = get_grader_llm()
    try:
        result = await llm.ainvoke(prompt)
    except Exception:
        logger.exception("Grader LLM call failed; defaulting to sufficient.")
        return GradeVerdict(verdict="sufficient", reasoning="grader_error")

    if isinstance(result, GradeVerdict):
        return result
    try:
        return GradeVerdict.model_validate(result)
    except Exception:
        logger.exception("Grader returned malformed output; defaulting to sufficient.")
        return GradeVerdict(verdict="sufficient", reasoning="grader_malformed")


@lru_cache(maxsize=1)
def get_grader_llm() -> Runnable:

    base = ChatGoogleGenerativeAI(
        model=settings.grader_model,
        google_api_key=settings.google_api_key,
        temperature=0,
    )
    return base.with_structured_output(GradeVerdict)
