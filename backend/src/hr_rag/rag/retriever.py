"""pgvector retriever over the HR document chunks table."""

from __future__ import annotations

from typing import Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hr_rag.config import settings
from hr_rag.db.document import Document, DocumentChunk
from hr_rag.db.session import async_session

# Embedding parity: the seed script (backend/scripts/seed_documents.py) calls
# aembed_documents without a task_type, so queries here use the same call to
# stay in the same vector space. If we ever re-seed with task_type=
# "RETRIEVAL_DOCUMENT", switch queries to task_type="RETRIEVAL_QUERY".


def _get_embedder() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key,
    )


async def _embed_query(query: str) -> list[float]:
    embedder = _get_embedder()
    [vector] = await embedder.aembed_documents([query])
    return vector


async def _run_search(
    session: AsyncSession, query_vec: list[float], top_k: int
) -> list[dict[str, Any]]:
    distance = DocumentChunk.embedding.cosine_distance(query_vec).label("distance")
    stmt = (
        select(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.document_id,
            DocumentChunk.chunk_index,
            DocumentChunk.chunk_text,
            Document.title,
            Document.source_uri,
            Document.doc_type,
            distance,
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(Document.status == "ready")
        .order_by(distance)
        .limit(top_k)
    )
    result = await session.execute(stmt)
    rows = result.mappings().all()
    min_sim = settings.retrieval_min_similarity
    chunks: list[dict[str, Any]] = []
    for row in rows:
        similarity = 1.0 - float(row["distance"])
        if similarity < min_sim:
            continue
        chunks.append(
            {
                "chunk_id": str(row["chunk_id"]),
                "document_id": str(row["document_id"]),
                "chunk_index": row["chunk_index"],
                "chunk_text": row["chunk_text"],
                "title": row["title"],
                "source_uri": row["source_uri"],
                "doc_type": row["doc_type"],
                "similarity": similarity,
            }
        )
    return chunks


async def retrieve_chunks(
    query: str,
    *,
    top_k: int | None = None,
    session: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """Vector-search top-k chunks for `query`.

    Returns a list of dicts ordered by descending similarity.
    """
    k = top_k or settings.retrieval_top_k
    query_vec = await _embed_query(query)
    if session is not None:
        return await _run_search(session, query_vec, k)
    async with async_session() as owned_session:
        return await _run_search(owned_session, query_vec, k)
