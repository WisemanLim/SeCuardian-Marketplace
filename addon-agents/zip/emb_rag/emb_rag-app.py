"""RAG 파이프라인 에이전트 — ADDON 판 (emb_rag).

내장 라우터 app/routers/router_rag.py (F-RAG) 의 ADDON 패키징.
로더가 /api/addon/emb_rag prefix 로 마운트한다.
설정은 내장판(settings.*) 대신 환경변수로 주입한다.
DB·임베딩 엔진 없이 인메모리 저장소(dict)로 동작 — 컬렉션 CRUD + 문서 수집 + 키워드 검색.
"""
import datetime
import os

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.deps import get_current_user

router = APIRouter(tags=["emb_rag"])

RAG_ENABLED = os.getenv("RAG_ENABLED", "true").lower() == "true"
RAG_MAX_COLLECTIONS = int(os.getenv("RAG_MAX_COLLECTIONS", "50"))
RAG_MAX_DOCS_PER_COLLECTION = int(os.getenv("RAG_MAX_DOCS_PER_COLLECTION", "500"))
RAG_DEFAULT_TOP_K = int(os.getenv("RAG_DEFAULT_TOP_K", "5"))

# 인메모리 저장소
_collections: dict[int, dict] = {}
_documents: dict[int, dict] = {}
_next_id: list[int] = [1]


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def _next() -> int:
    v = _next_id[0]
    _next_id[0] += 1
    return v


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    sensitivity: str = "general"


class DocumentIn(BaseModel):
    title: str = ""
    source: str = ""
    text: str = Field(min_length=1)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


def _keyword_search(collection_id: int, query: str, top_k: int) -> list[dict]:
    """단순 키워드 검색 (ADDON 인메모리 버전 — 실 임베딩 없음)."""
    terms = query.lower().split()
    hits = []
    for doc in _documents.values():
        if doc.get("collection_id") != collection_id:
            continue
        text_lower = doc.get("text", "").lower()
        score = sum(1 for t in terms if t in text_lower)
        if score > 0:
            hits.append({"document_id": doc["id"], "title": doc.get("title", ""),
                         "text": doc.get("text", "")[:300], "score": score})
    hits.sort(key=lambda h: h["score"], reverse=True)
    return hits[:top_k]


@router.get("/status")
async def rag_status(_: dict = Depends(get_current_user)):
    """RAG 에이전트 상태."""
    total_docs = len(_documents)
    return {
        "rag_enabled": RAG_ENABLED,
        "collections_count": len(_collections),
        "documents_count": total_docs,
        "default_top_k": RAG_DEFAULT_TOP_K,
        "source": "emb_rag (in-memory ADDON, keyword search)",
    }


@router.get("/collections")
async def list_collections(_: dict = Depends(get_current_user)):
    """RAG 컬렉션 목록."""
    result = []
    for coll in _collections.values():
        doc_count = sum(1 for d in _documents.values() if d["collection_id"] == coll["id"])
        result.append({**coll, "document_count": doc_count})
    return {"collections": result}


@router.post("/collections", status_code=201)
async def create_collection(body: CollectionCreate, _: dict = Depends(get_current_user)):
    """RAG 컬렉션 생성."""
    if body.sensitivity not in ("general", "sensitive"):
        raise HTTPException(422, "sensitivity must be 'general' or 'sensitive'")
    if len(_collections) >= RAG_MAX_COLLECTIONS:
        raise HTTPException(429, "max collections reached")
    dup = next((c for c in _collections.values() if c["name"] == body.name), None)
    if dup:
        raise HTTPException(409, f"collection '{body.name}' already exists")
    cid = _next()
    coll = {
        "id": cid,
        "name": body.name,
        "description": body.description,
        "sensitivity": body.sensitivity,
        "created_at": _now(),
    }
    _collections[cid] = coll
    return coll


@router.get("/collections/{collection_id}")
async def get_collection(collection_id: int, _: dict = Depends(get_current_user)):
    """컬렉션 단건 조회."""
    coll = _collections.get(collection_id)
    if not coll:
        raise HTTPException(404, "collection not found")
    doc_count = sum(1 for d in _documents.values() if d["collection_id"] == collection_id)
    return {**coll, "document_count": doc_count}


@router.post("/collections/{collection_id}/documents", status_code=201)
async def ingest_document(
    collection_id: int,
    body: DocumentIn,
    _: dict = Depends(get_current_user),
):
    """문서 수집 — 컬렉션에 문서를 추가."""
    if collection_id not in _collections:
        raise HTTPException(404, "collection not found")
    coll_docs = sum(1 for d in _documents.values() if d["collection_id"] == collection_id)
    if coll_docs >= RAG_MAX_DOCS_PER_COLLECTION:
        raise HTTPException(429, "max documents per collection reached")
    did = _next()
    doc = {
        "id": did,
        "collection_id": collection_id,
        "title": body.title,
        "source": body.source,
        "text": body.text,
        "chunk_count": max(1, len(body.text) // 512),
        "ingested_at": _now(),
    }
    _documents[did] = doc
    return {"id": did, "collection_id": collection_id, "title": body.title, "chunks": doc["chunk_count"]}


@router.get("/collections/{collection_id}/documents")
async def list_documents(
    collection_id: int,
    limit: int = Query(50, ge=1, le=200),
    _: dict = Depends(get_current_user),
):
    """컬렉션 내 문서 목록."""
    if collection_id not in _collections:
        raise HTTPException(404, "collection not found")
    docs = [
        {"id": d["id"], "collection_id": d["collection_id"], "title": d["title"],
         "source": d["source"], "chunks": d["chunk_count"]}
        for d in _documents.values()
        if d["collection_id"] == collection_id
    ]
    return {"collection_id": collection_id, "documents": docs[:limit]}


@router.post("/collections/{collection_id}/search")
async def search(
    collection_id: int,
    body: SearchRequest,
    _: dict = Depends(get_current_user),
):
    """하이브리드 검색 (ADDON 판: 키워드 기반 스텁)."""
    if collection_id not in _collections:
        raise HTTPException(404, "collection not found")
    hits = _keyword_search(collection_id, body.query, body.top_k)
    return {
        "collection_id": collection_id,
        "query": body.query,
        "top_k": body.top_k,
        "hits": hits,
        "note": "ADDON in-memory keyword search — no embeddings",
    }
