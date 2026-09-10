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


_qdrant_client_cache = None
_qdrant_tried = False


def resolve() -> str:
    """활성 벡터 백엔드: 'pgvector' | 'qdrant' | 'local'. 조건 미충족 시 항상 'local' 폴백."""
    if settings.vector_backend == "pgvector" and not _IS_SQLITE:
        try:
            import pgvector  # noqa: F401 — 설치 확인용
            return "pgvector"
        except Exception:  # noqa: BLE001
            logger.warning("[vector_backend] pgvector 라이브러리 없음 → local 폴백")
    elif settings.vector_backend == "qdrant":
        # qdrant-client 는 선택 의존(오프라인/폐쇄망 기본은 미설치). 없으면 local 폴백.
        if _qdrant_client() is not None:
            return "qdrant"
        logger.warning("[vector_backend] qdrant-client 미설치/미구성 → local 폴백")
    return "local"


def _qdrant_client():
    """QdrantClient 지연 생성·캐시. 미설치/생성 실패 시 None(→ local 폴백)."""
    global _qdrant_client_cache, _qdrant_tried
    if _qdrant_client_cache is not None:
        return _qdrant_client_cache
    if _qdrant_tried:
        return None
    _qdrant_tried = True
    try:
        from qdrant_client import QdrantClient  # 선택 의존
        _qdrant_client_cache = QdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
            timeout=5.0,
        )
        return _qdrant_client_cache
    except Exception:  # noqa: BLE001 — 미설치/URL 불량 등
        return None


def _qdrant_collection() -> str:
    return settings.qdrant_collection or "secmp_rag"


async def ensure_pg_schema(embedding_dim: int) -> None:
    """활성 백엔드 스키마 보장. pgvector=vector 컬럼/인덱스, qdrant=컬렉션. local=no-op. 멱등."""
    backend = resolve()
    if backend == "qdrant":
        _ensure_qdrant_collection(embedding_dim)
        return
    if backend != "pgvector":
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


async def write_embedding(chunk_id: int, vec: list[float], collection_id: int | None = None) -> None:
    """청크 임베딩 기록. pgvector=vector 컬럼, qdrant=포인트 upsert(payload.collection_id).
    local 이면 no-op(embedding_json 사용). collection_id 는 qdrant payload 필터용(선택)."""
    backend = resolve()
    if backend == "qdrant":
        _qdrant_upsert(chunk_id, vec, collection_id)
        return
    if backend != "pgvector":
        return
    try:
        await execute_write(
            f"UPDATE rag_chunks SET embedding = {_PH} WHERE id = {_PH}",
            (json.dumps(vec), chunk_id),  # pgvector 는 '[...]' 텍스트 리터럴 캐스팅 허용
        )
    except Exception:  # noqa: BLE001
        logger.exception("[vector_backend] embedding 기록 실패(chunk=%s)", chunk_id)


async def dense_scores(collection_id: int, q_vec: list[float], top_k: int) -> dict[int, float] | None:
    """dense 점수({chunk_id: score}) 반환. pgvector=SQL 코사인, qdrant=검색. local 이면 None(호출측 폴백)."""
    backend = resolve()
    if backend == "qdrant":
        return _qdrant_search(collection_id, q_vec, top_k)
    if backend != "pgvector":
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


# ─── Qdrant 경로 (선택 의존 qdrant-client, 실패 시 조용히 no-op/None → local 폴백) ───

def _ensure_qdrant_collection(embedding_dim: int) -> None:
    """단일 컬렉션(COSINE, size=embedding_dim) 보장. 멱등."""
    client = _qdrant_client()
    if client is None:
        return
    try:
        from qdrant_client.models import Distance, VectorParams
        name = _qdrant_collection()
        existing = {c.name for c in client.get_collections().collections}
        if name not in existing:
            client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=embedding_dim, distance=Distance.COSINE),
            )
    except Exception:  # noqa: BLE001 — 서버 미기동/권한 등 → 무중단(local 폴백)
        logger.warning("[vector_backend] qdrant 컬렉션 보장 실패 → local 폴백")


def _qdrant_upsert(chunk_id: int, vec: list[float], collection_id: int | None) -> None:
    client = _qdrant_client()
    if client is None:
        return
    try:
        from qdrant_client.models import PointStruct
        client.upsert(
            collection_name=_qdrant_collection(),
            points=[PointStruct(id=chunk_id, vector=vec, payload={"collection_id": collection_id})],
        )
    except Exception:  # noqa: BLE001
        logger.warning("[vector_backend] qdrant upsert 실패(chunk=%s)", chunk_id)


def _qdrant_search(collection_id: int, q_vec: list[float], top_k: int):
    """payload.collection_id 필터로 검색 → {chunk_id: score}. 실패 시 None(로컬 폴백)."""
    client = _qdrant_client()
    if client is None:
        return None
    try:
        from qdrant_client.models import FieldCondition, Filter, MatchValue
        hits = client.search(
            collection_name=_qdrant_collection(),
            query_vector=q_vec,
            query_filter=Filter(must=[FieldCondition(key="collection_id", match=MatchValue(value=collection_id))]),
            limit=top_k,
        )
        return {int(h.id): float(h.score) for h in hits if h.score and h.score > 0}
    except Exception:  # noqa: BLE001
        logger.warning("[vector_backend] qdrant 검색 실패(collection=%s)", collection_id)
        return None
