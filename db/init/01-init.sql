-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Enable uuid extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create documents table for RAG
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(768),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for vector similarity search
CREATE INDEX IF NOT EXISTS documents_embedding_idx
    ON documents USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
