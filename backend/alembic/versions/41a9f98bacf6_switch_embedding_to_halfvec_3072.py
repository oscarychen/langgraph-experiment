"""switch embedding to halfvec 3072

Revision ID: 41a9f98bacf6
Revises: 384406161d17
Create Date: 2026-05-10 22:45:55.385173

"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "41a9f98bacf6"
down_revision: Union[str, Sequence[str], None] = "384406161d17"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema.

    Switch embeddings from Vector(768) to HALFVEC(3072). pgvector caps HNSW
    on the `vector` type at 2000 dims; halfvec (float16) supports up to 4000.
    Any existing embeddings are dropped — they were produced by a different
    model and dimension and cannot be converted in-place. Re-run db-seed to
    repopulate.
    """
    op.drop_index(
        "ix_document_chunks_embedding_hnsw",
        table_name="document_chunks",
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.execute("ALTER TABLE document_chunks DROP COLUMN embedding")
    op.execute(
        "ALTER TABLE document_chunks ADD COLUMN embedding halfvec(3072) NOT NULL"
    )
    op.create_index(
        "ix_document_chunks_embedding_hnsw",
        "document_chunks",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "halfvec_cosine_ops"},
    )


def downgrade() -> None:
    """Downgrade schema. Same caveat as upgrade — existing embeddings lost."""
    op.drop_index(
        "ix_document_chunks_embedding_hnsw",
        table_name="document_chunks",
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "halfvec_cosine_ops"},
    )
    op.execute("ALTER TABLE document_chunks DROP COLUMN embedding")
    op.execute(
        "ALTER TABLE document_chunks ADD COLUMN embedding vector(768) NOT NULL"
    )
    op.create_index(
        "ix_document_chunks_embedding_hnsw",
        "document_chunks",
        ["embedding"],
        unique=False,
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )