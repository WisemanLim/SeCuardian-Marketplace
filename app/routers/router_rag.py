"""router_rag (F-RAG) — /api/rag.

컬렉션 생성/조회 + 문서 수집(ingest) + 하이브리드 검색. SeCuardian Path A 준용.
민감 컬렉션 분리(sensitivity), tenant_id 격리. 등록/수집은 admin/supervisor.

참조: SeCuardian-Marketplace-v0 router_rag 를 async raw-SQL 로 이식.
"""
from dataclasses import asdict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_current_user, require_role
from app.db import _PH, execute_insert, fetch_all, fetch_one
from app.services.rag_pipeline import hybrid_search, index_document

router = APIRouter(prefix="/api/rag", tags=["rag"])


def _tenant() -> str:
    return settings.tenant_default_id or "default"


class CollectionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str = ""
    sensitivity: str = "general"  # general | sensitive


class DocumentIn(BaseModel):
    title: str = ""
    source: str = ""
    text: str = Field(min_length=1)


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = None


async def _get_coll(collection_id: int, tid: str) -> dict:
    coll = await fetch_one(
        f"SELECT * FROM rag_collections WHERE id = {_PH} AND tenant_id = {_PH}", (collection_id, tid)
    )
    if not coll:
        raise HTTPException(404, "collection not found")
    return coll


@router.get("/collections")
async def list_collections(user: dict = Depends(get_current_user)):
    rows = await fetch_all(
        f"SELECT * FROM rag_collections WHERE tenant_id = {_PH} ORDER BY id", (_tenant(),)
    )
    return {"collections": rows}


@router.post("/collections", status_code=201)
async def create_collection(body: CollectionCreate, user: dict = Depends(require_role("admin", "supervisor"))):
    if body.sensitivity not in ("general", "sensitive"):
        raise HTTPException(422, "sensitivity must be 'general' or 'sensitive'")
    tid = _tenant()
    dup = await fetch_one(
        f"SELECT id FROM rag_collections WHERE name = {_PH} AND tenant_id = {_PH}", (body.name, tid)
    )
    if dup:
        raise HTTPException(409, f"collection '{body.name}' already exists")
    cid = await execute_insert(
        f"INSERT INTO rag_collections (tenant_id, name, description, sensitivity, embedding_dim) "
        f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH})",
        (tid, body.name, body.description, body.sensitivity, settings.rag_embedding_dim),
    )
    return await _get_coll(cid, tid)


@router.post("/collections/{collection_id}/documents", status_code=201)
async def ingest_document(
    collection_id: int, body: DocumentIn, user: dict = Depends(require_role("admin", "supervisor"))
):
    tid = _tenant()
    coll = await _get_coll(collection_id, tid)
    did = await execute_insert(
        f"INSERT INTO rag_documents (tenant_id, collection_id, title, source, text) "
        f"VALUES ({_PH}, {_PH}, {_PH}, {_PH}, {_PH})",
        (tid, coll["id"], body.title, body.source, body.text),
    )
    n = await index_document(tid, coll["id"], coll["embedding_dim"], did, body.text)
    doc = await fetch_one(f"SELECT id, collection_id, title, source FROM rag_documents WHERE id = {_PH}", (did,))
    return {**doc, "chunks": n}


@router.get("/collections/{collection_id}/documents")
async def list_documents(collection_id: int, user: dict = Depends(get_current_user)):
    tid = _tenant()
    coll = await _get_coll(collection_id, tid)
    docs = await fetch_all(
        f"SELECT id, collection_id, title, source FROM rag_documents WHERE collection_id = {_PH} ORDER BY id",
        (coll["id"],),
    )
    result = []
    for d in docs:
        cnt = await fetch_one(f"SELECT COUNT(*) AS n FROM rag_chunks WHERE document_id = {_PH}", (d["id"],))
        result.append({**d, "chunks": (cnt or {}).get("n", 0)})
    return {"documents": result}


@router.post("/collections/{collection_id}/search")
async def search(collection_id: int, body: SearchRequest, user: dict = Depends(get_current_user)):
    tid = _tenant()
    coll = await _get_coll(collection_id, tid)
    hits = await hybrid_search(coll["id"], coll["embedding_dim"], body.query, body.top_k)
    return {"hits": [asdict(h) for h in hits]}
