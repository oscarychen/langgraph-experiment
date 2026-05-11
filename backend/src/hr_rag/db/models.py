"""Model registry. Import all model modules here so Base.metadata is complete."""

# ruff: noqa: F401
from hr_rag.db.base import Base
from hr_rag.db.document import Document, DocumentChunk
