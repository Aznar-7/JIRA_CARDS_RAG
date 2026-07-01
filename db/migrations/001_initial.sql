-- db/migrations/001_initial.sql

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS issues (
    id            SERIAL PRIMARY KEY,
    issue_key     TEXT UNIQUE NOT NULL,
    title         TEXT,
    issue_type    TEXT,
    status        TEXT,
    priority      TEXT,
    sprint        TEXT,
    glpi_ticket   TEXT,
    focus_area    TEXT,
    assignee      TEXT,
    reporter      TEXT,
    resolved_by   TEXT,
    created_at    TIMESTAMPTZ,
    updated_at    TIMESTAMPTZ,
    resolved_at   TIMESTAMPTZ,
    jira_url      TEXT,
    ingested_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chunks (
    id          SERIAL PRIMARY KEY,
    chunk_id    TEXT UNIQUE NOT NULL,
    issue_key   TEXT NOT NULL REFERENCES issues(issue_key) ON DELETE CASCADE,
    chunk_type  TEXT NOT NULL,
    text        TEXT NOT NULL,
    embedding   vector(384),
    metadata    JSONB,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

-- HNSW index: works at any dataset size (no minimum rows like ivfflat)
CREATE INDEX IF NOT EXISTS chunks_embedding_hnsw_idx
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Trigram index for fast keyword/partial matching
CREATE INDEX IF NOT EXISTS chunks_text_trgm_idx
    ON chunks USING gin (text gin_trgm_ops);

CREATE INDEX IF NOT EXISTS chunks_issue_key_idx ON chunks (issue_key);
CREATE INDEX IF NOT EXISTS issues_status_idx ON issues (status);
CREATE INDEX IF NOT EXISTS issues_sprint_idx ON issues (sprint);
