"""Vector 백엔드 어댑터 (F-RAG, PRD §7.5).

`VECTOR_BACKEND=pgvector` + PostgreSQL + pgvector 라이브러리가 모두 갖춰지면 pgvector 경로(SQL `<=>`
코사인 거리 ANN)를 쓰고, 그 외(로컬 sqlite·미설치·미설정)에는 기존 로컬 해싱 임베더 + 파이썬 코사인
(`rag_pipeline`)으로 **자동 폴백**한다. 온프렘 기본은 pgvector(§7.5), 개발/로컬은 sqlite.

pgvector 실동작은 PostgreSQL + `CREATE EXTENSION vector` 가 필요하므로 이 세션(sqlite)에서는
resolve()="local" 로 폴백 검증만 가능. pg 경로 코드는 postgres 환경에서 활성화된다.
"""
import json
import logging

from app.core.config import settings
from app.db import _IS_SQLITE, _PH, execute_write, fetch_all

logger = logging.getLogger("uvicorn.error")


def resolve() -> str:
    """활성 벡터 백엔드: 'pgvector' | 'local'. 조건 미충족 시 항상 'local' 폴백."""
    if settings.vector_backend == "pgvector" and not _IS_SQLITE:
        try:
            import pgvector  # noqa: F401 — 설치 확인용
            return "pgvector"
        except Exception:  # noqa: BLE001
            logger.warning("[vector_backend] pgvector 라이브러리 없음 → local 폴백")
    return "local"


async def ensure_pg_schema(embedding_dim: int) -> None:
    """(pgvector 전용) vector 확장 + rag_chunks.embedding 컬럼·IVFFLAT 인덱스 보장. 멱등."""
    if resolve() != "pgvector":
        return
    try:
        await execute_write("CREATE EXTENSION IF NOT EXISTS vector")
        await execute_write(f"ALTER TABLE rag_chunks ADD COLUMN IF NOT EXISTS embedding vector({embedding_dim})")
        await execute_write(
            "CREATE INDEX IF NOT EXISTS idx_rag_chunks_embedding ON rag_chunks "
            "USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
        )
    except Exception:  # noqa: BLE001 — 스키마 보장 실패 시 로컬 폴백(무중단)
        logger.exception("[vector_backend] pgvector 스키마 보장 실패")


async def write_embedding(chunk_id: int, vec: list[float]) -> None:
    """(pgvector 전용) 청크 임베딩을 vector 컬럼에 기록. local 이면 no-op(embedding_json 사용)."""
    if resolve() != "pgvector":
        return
    try:
        await execute_write(
            f"UPDATE rag_chunks SET embedding = {_PH} WHERE id = {_PH}",
            (json.dumps(vec), chunk_id),  # pgvector 는 '[...]' 텍스트 리터럴 캐스팅 허용
        )
    except Exception:  # noqa: BLE001
        logger.exception("[vector_backend] embedding 기록 실패(chunk=%s)", chunk_id)


async def dense_scores(collection_id: int, q_vec: list[float], top_k: int) -> dict[int, float] | None:
    """(pgvector 전용) SQL 코사인 거리로 dense 점수 반환({chunk_id: score}). local 이면 None(호출측 폴백)."""
    if resolve() != "pgvector":
        return None
    try:
        rows = await fetch_all(
            f"SELECT id, 1 - (embedding <=> {_PH}) AS score FROM rag_chunks "
            f"WHERE collection_id = {_PH} AND embedding IS NOT NULL "
            f"ORDER BY embedding <=> {_PH} LIMIT {_PH}",
            (json.dumps(q_vec), collection_id, json.dumps(q_vec), top_k),
        )
        return {r["id"]: float(r["score"]) for r in rows if r.get("score", 0) > 0}
    except Exception:  # noqa: BLE001 — 쿼리 실패 시 None → 로컬 폴백
        logger.exception("[vector_backend] pgvector dense 쿼리 실패")
        return None
