"""Seed the database with mock HR policy documents.

Idempotent: skips documents whose (source_uri, version) already exist.
Soft-fails if GOOGLE_API_KEY is not set so `make setup` can complete on a
fresh checkout.
"""

import asyncio
import sys
from datetime import UTC, datetime

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from sqlalchemy import select

from hr_rag.config import settings
from hr_rag.db.document import Document, DocumentChunk
from hr_rag.db.session import async_session

DOCUMENTS = [
    {
        "source_uri": "seed://hr-policy/leave",
        "title": "Leave Policy",
        "doc_type": "leave",
        "summary": (
            "Vacation accrual, sick leave, parental leave, and request-notice "
            "requirements."
        ),
        "content": (
            "Full-time employees accrue 1.5 days of vacation per month (18 days/year). "
            "Employees in their first year accrue at a prorated rate. Up to 5 unused "
            "days may be carried over into the following year. Sick leave is separate: "
            "10 days per year, non-accruing. Parental leave is 16 weeks fully paid for "
            "primary caregivers and 6 weeks for secondary caregivers. Leave requests "
            "must be submitted at least 2 weeks in advance for planned absences."
        ),
    },
    {
        "source_uri": "seed://hr-policy/benefits",
        "title": "Health Benefits",
        "doc_type": "benefits",
        "summary": (
            "Health plan tiers, employer premium share, dental/vision add-ons, HSA, "
            "and open enrollment."
        ),
        "content": (
            "Employees are eligible for health benefits from day one of employment. "
            "Three tiers are available: Basic, Standard, and Premium. The company "
            "covers 80% of the Standard tier premium. Dental and vision are optional "
            "add-ons. A Health Savings Account (HSA) is available for employees on "
            "high-deductible plans. Open enrollment is held each November for the "
            "following calendar year."
        ),
    },
    {
        "source_uri": "seed://hr-policy/remote-work",
        "title": "Remote Work Policy",
        "doc_type": "remote-work",
        "summary": (
            "Hybrid limits, fully remote approval, core hours, and equipment stipend."
        ),
        "content": (
            "Employees may work remotely up to 3 days per week with manager approval. "
            "Fully remote arrangements require VP-level sign-off and are reviewed "
            "annually. Employees working remotely are expected to be online and "
            "responsive during core hours (10 AM to 3 PM local time). Home office "
            "equipment stipends of $750 are available annually."
        ),
    },
]


async def main() -> int:
    if not settings.google_api_key:
        print(
            "[seed] GOOGLE_API_KEY is not set; skipping document seed.\n"
            "       Set it in .env and re-run `make db-seed` to populate documents.",
            file=sys.stderr,
        )
        return 0

    embedder = GoogleGenerativeAIEmbeddings(
        model=settings.embedding_model,
        google_api_key=settings.google_api_key,
    )

    seeded = 0
    skipped = 0

    async with async_session() as session:
        for doc in DOCUMENTS:
            existing = await session.scalar(
                select(Document).where(
                    Document.source_uri == doc["source_uri"],
                    Document.version == "1",
                )
            )
            if existing is not None:
                print(f"[seed] skip {doc['source_uri']} (already seeded)")
                skipped += 1
                continue

            [vector] = await embedder.aembed_documents([doc["content"]])

            document = Document(
                title=doc["title"],
                summary=doc["summary"],
                source_uri=doc["source_uri"],
                doc_type=doc["doc_type"],
                version="1",
                language="en",
                status="ready",
                ingested_at=datetime.now(UTC),
                metadata_={"seed": True},
            )
            document.chunks.append(
                DocumentChunk(
                    chunk_index=0,
                    chunk_text=doc["content"],
                    embedding=vector,
                    embedding_model=settings.embedding_model,
                )
            )
            session.add(document)
            print(f"[seed] seeded {doc['source_uri']}")
            seeded += 1

        await session.commit()

    print(f"[seed] done. seeded={seeded} skipped={skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
