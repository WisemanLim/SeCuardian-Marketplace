-- grafana-dashboard RAG Agent 테이블 스키마
-- tbl_grafanadashboard_documents: 인제스트된 원본 문서 (Grafana 패널 포함)
-- tbl_grafanadashboard_chunks: 청킹 + 임베딩 결과

CREATE TABLE IF NOT EXISTS tbl_grafanadashboard_documents (
    id             SERIAL PRIMARY KEY,
    filename       VARCHAR(500) NOT NULL,
    content        TEXT,
    uploaded_by    VARCHAR(50),
    dashboard_uid  VARCHAR(100),
    panel_title    VARCHAR(500),
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tbl_grafanadashboard_chunks (
    id             SERIAL PRIMARY KEY,
    doc_id         INTEGER      NOT NULL REFERENCES tbl_grafanadashboard_documents(id) ON DELETE CASCADE,
    chunk_index    INTEGER      NOT NULL DEFAULT 0,
    content        TEXT         NOT NULL,
    embedding_json TEXT,
    created_at     TIMESTAMP    NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_grafanadashboard_chunks_doc_id ON tbl_grafanadashboard_chunks(doc_id);
CREATE INDEX IF NOT EXISTS idx_grafanadashboard_docs_uid ON tbl_grafanadashboard_documents(dashboard_uid);
