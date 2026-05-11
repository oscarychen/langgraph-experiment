"""DB + embeddings integration test for retrieve_chunks.

Skipped when GOOGLE_API_KEY or the database aren't configured so unit-test
runs on fresh checkouts don't fail.
"""

import os
from datetime import UTC, datetime

import pytest
from sqlalchemy import select

from hr_rag.config import settings
from hr_rag.db.document import Document, DocumentChunk
from hr_rag.db.session import async_session
from hr_rag.rag.retriever import _embed_query, retrieve_chunks

pytestmark = pytest.mark.skipif(
    not (settings.google_api_key or os.environ.get("GOOGLE_API_KEY")),
    reason="needs GOOGLE_API_KEY",
)


async def _ensure_seed_doc(session, source_uri: str, content: str) -> None:
    existing = await session.scalar(
        select(Document).where(Document.source_uri == source_uri)
    )
    if existing is not None:
        return
    vector = await _embed_query(content)
    doc = Document(
        title="Test Leave Policy",
        summary="test",
        source_uri=source_uri,
        doc_type="leave",
        version="1",
        language="en",
        status="ready",
        ingested_at=datetime.now(UTC),
        metadata_={"test": True},
    )
    doc.chunks.append(
        DocumentChunk(
            chunk_index=0,
            chunk_text=content,
            embedding=vector,
            embedding_model=settings.embedding_model,
        )
    )
    session.add(doc)
    await session.commit()


async def test_retrieve_chunks_returns_seeded_doc():
    source_uri = "test://retriever/leave"
    content = (
        "Full-time employees accrue 1.5 days of vacation per month. "
        "Up to 5 unused days carry over."
    )
    try:
        async with async_session() as session:
            await _ensure_seed_doc(session, source_uri, content)
    except Exception as exc:  # noqa: BLE001
        pytest.skip(f"database unavailable: {exc}")

    chunks = await retrieve_chunks("vacation accrual per month", top_k=3)
    assert chunks, "expected at least one chunk"
    assert any(c.get("source_uri") == source_uri for c in chunks)
    top = chunks[0]
    assert top["similarity"] > 0.3
    assert "chunk_text" in top
