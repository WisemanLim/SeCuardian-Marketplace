"""grafana-dashboard — Grafana 패널 임베딩 + 벡터 검색 기반 RAG Agent.

마운트 경로: /api/addon/grafana-dashboard/...
엔드포인트:
  POST /ingest               문서 업로드 + 청킹 + 임베딩
  GET  /documents            인제스트된 문서 목록
  DELETE /documents/{id}     문서 삭제
  POST /search               벡터 유사도 검색 (코사인 유사도)
  POST /qa                   RAG 기반 Q&A (SSE 스트리밍)
  POST /sync/grafana         Grafana API에서 패널 정보 동기화 (supervisor/admin)
  GET  /dashboards           동기화된 Grafana 대시보드 목록
"""
import json
import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.core.deps import get_current_user, require_role
from app.db import _PH, execute_insert, execute_write, fetch_all, fetch_one

router = APIRouter(tags=["grafana-dashboard"])

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")
GRAFANA_SERVICE_TOKEN = os.getenv("GRAFANA_SERVICE_TOKEN", "")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")


# ─── 임베딩 함수 ──────────────────────────────────────────────────────────────

async def _embed(text: str) -> list[float]:
    """텍스트를 임베딩 벡터로 변환합니다.
    Ollama nomic-embed-text를 먼저 시도하고, 실패 시 해시 기반 벡터로 폴백합니다.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text},
            )
            if resp.status_code == 200:
                data = resp.json()
                return data["embedding"]
    except Exception:
        pass

    # 폴백: 해시 기반 128차원 벡터
    words = text.lower().split()
    freq: dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    vec = [0.0] * 128
    for w, cnt in freq.items():
        idx = hash(w) % 128
        vec[idx] += cnt
    norm = (sum(x * x for x in vec) ** 0.5) or 1.0
    return [x / norm for x in vec]


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = (sum(x * x for x in a) ** 0.5) or 1.0
    nb = (sum(x * x for x in b) ** 0.5) or 1.0
    return dot / (na * nb)


# ─── 문서 인제스트 ────────────────────────────────────────────────────────────

@router.post("/ingest", status_code=201)
async def ingest_document(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    """문서를 업로드하고 청킹·임베딩 후 저장합니다."""
    content = (await file.read()).decode("utf-8", errors="ignore")
    filename = file.filename or "unknown"

    doc_id = await execute_insert(
        f"INSERT INTO tbl_grafanadashboard_documents (filename, content, uploaded_by) "
        f"VALUES ({_PH},{_PH},{_PH})",
        (filename, content[:10000], user.get("sub", "")),
    )

    chunks = _chunk_text(content)
    for idx, chunk in enumerate(chunks):
        vec = await _embed(chunk)
        await execute_write(
            f"INSERT INTO tbl_grafanadashboard_chunks (doc_id, chunk_index, content, embedding_json) "
            f"VALUES ({_PH},{_PH},{_PH},{_PH})",
            (doc_id, idx, chunk, json.dumps(vec)),
        )

    return {"doc_id": doc_id, "filename": filename, "chunks": len(chunks)}


class IngestTextRequest(BaseModel):
    content: str
    filename: str = "manual-input.txt"


@router.post("/ingest-text", status_code=201)
async def ingest_text(body: IngestTextRequest, user: dict = Depends(get_current_user)):
    """텍스트 본문을 직접 청킹·임베딩 후 저장합니다 (JSON — AI 어시스턴트용)."""
    doc_id = await execute_insert(
        f"INSERT INTO tbl_grafanadashboard_documents (filename, content, uploaded_by) "
        f"VALUES ({_PH},{_PH},{_PH})",
        (body.filename, body.content[:10000], user.get("sub", "")),
    )
    chunks = _chunk_text(body.content)
    for idx, chunk in enumerate(chunks):
        vec = await _embed(chunk)
        await execute_write(
            f"INSERT INTO tbl_grafanadashboard_chunks (doc_id, chunk_index, content, embedding_json) "
            f"VALUES ({_PH},{_PH},{_PH},{_PH})",
            (doc_id, idx, chunk, json.dumps(vec)),
        )
    return {"doc_id": doc_id, "filename": body.filename, "chunks": len(chunks)}


@router.get("/documents")
async def list_documents(user: dict = Depends(get_current_user)):
    rows = await fetch_all(
        "SELECT id, filename, uploaded_by, dashboard_uid, panel_title, created_at "
        "FROM tbl_grafanadashboard_documents ORDER BY created_at DESC"
    )
    return {"documents": rows, "total": len(rows)}


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: int,
    user: dict = Depends(require_role("supervisor", "admin")),
):
    await execute_write(
        f"DELETE FROM tbl_grafanadashboard_chunks WHERE doc_id = {_PH}", (doc_id,)
    )
    await execute_write(
        f"DELETE FROM tbl_grafanadashboard_documents WHERE id = {_PH}", (doc_id,)
    )
    return {"message": f"문서 {doc_id} 삭제 완료"}


# ─── 검색 ────────────────────────────────────────────────────────────────────

class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


@router.post("/search")
async def search(body: SearchRequest, user: dict = Depends(get_current_user)):
    """쿼리와 유사한 문서 청크를 코사인 유사도로 검색합니다."""
    query_vec = await _embed(body.query)
    chunks = await fetch_all(
        "SELECT c.id, c.doc_id, c.content, c.embedding_json, d.filename, "
        "d.dashboard_uid, d.panel_title "
        "FROM tbl_grafanadashboard_chunks c "
        "JOIN tbl_grafanadashboard_documents d ON c.doc_id = d.id"
    )
    scored = []
    for chunk in chunks:
        try:
            vec = json.loads(chunk["embedding_json"])
            sim = _cosine_sim(query_vec, vec)
            scored.append({**chunk, "score": round(sim, 4), "embedding_json": None})
        except Exception:
            pass
    scored.sort(key=lambda x: x["score"], reverse=True)
    return {"results": scored[: body.top_k], "query": body.query}


# ─── Q&A (RAG) ───────────────────────────────────────────────────────────────

class QARequest(BaseModel):
    question: str
    top_k: int = 3


@router.post("/qa")
async def qa(body: QARequest, user: dict = Depends(get_current_user)):
    """RAG 기반 Q&A — 관련 청크 검색 후 SSE 스트리밍 답변."""
    query_vec = await _embed(body.question)
    chunks = await fetch_all(
        "SELECT c.content, c.embedding_json, d.filename, d.dashboard_uid, d.panel_title "
        "FROM tbl_grafanadashboard_chunks c "
        "JOIN tbl_grafanadashboard_documents d ON c.doc_id = d.id"
    )
    scored = []
    for chunk in chunks:
        try:
            vec = json.loads(chunk["embedding_json"])
            sim = _cosine_sim(query_vec, vec)
            scored.append({
                "content": chunk["content"],
                "filename": chunk["filename"],
                "dashboard_uid": chunk.get("dashboard_uid"),
                "panel_title": chunk.get("panel_title"),
                "score": sim,
            })
        except Exception:
            pass
    scored.sort(key=lambda x: x["score"], reverse=True)
    top_chunks = scored[: body.top_k]

    context = "\n\n".join(
        f"[{c['filename']} / {c.get('panel_title') or 'N/A'}]\n{c['content']}"
        for c in top_chunks
    )

    async def _gen():
        yield f"data: {json.dumps({'event': 'context', 'sources': [{'filename': c['filename'], 'dashboard_uid': c.get('dashboard_uid'), 'panel_title': c.get('panel_title'), 'score': round(c['score'], 4)} for c in top_chunks]})}\n\n"

        answer = (
            f"질문: {body.question}\n\n"
            f"Grafana 대시보드 정보를 기반으로 답변합니다.\n\n"
            f"[참고 컨텍스트]\n{context[:800]}...\n\n"
            "실제 서비스에서는 이 부분을 LLM(Anthropic/OpenAI) 호출로 교체하세요."
        )
        yield f"data: {json.dumps({'event': 'answer', 'text': answer})}\n\n"
        yield f"data: {json.dumps({'event': 'done'})}\n\n"

    return StreamingResponse(_gen(), media_type="text/event-stream")


# ─── Grafana 동기화 ───────────────────────────────────────────────────────────

@router.post("/sync/grafana", status_code=200)
async def sync_grafana(
    user: dict = Depends(require_role("supervisor", "admin")),
):
    """Grafana API에서 대시보드 패널 정보를 가져와 문서로 인제스트합니다."""
    if not GRAFANA_SERVICE_TOKEN:
        raise HTTPException(status_code=400, detail="GRAFANA_SERVICE_TOKEN이 설정되지 않았습니다.")

    headers = {"Authorization": f"Bearer {GRAFANA_SERVICE_TOKEN}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. 대시보드 목록 조회
        search_resp = await client.get(
            f"{GRAFANA_URL}/api/search",
            params={"type": "dash-db"},
            headers=headers,
        )
        if search_resp.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Grafana API 오류: {search_resp.status_code}",
            )
        dashboards = search_resp.json()

        ingested = []
        errors = []

        for dash in dashboards:
            uid = dash.get("uid")
            title = dash.get("title", "Untitled")
            if not uid:
                continue

            # 2. 각 대시보드 상세 조회
            try:
                detail_resp = await client.get(
                    f"{GRAFANA_URL}/api/dashboards/uid/{uid}",
                    headers=headers,
                )
                if detail_resp.status_code != 200:
                    errors.append({"uid": uid, "error": f"HTTP {detail_resp.status_code}"})
                    continue

                detail = detail_resp.json()
                dashboard_model = detail.get("dashboard", {})
                panels = dashboard_model.get("panels", [])

                for panel in panels:
                    panel_title = panel.get("title", "Untitled Panel")
                    description = panel.get("description", "")
                    panel_type = panel.get("type", "")

                    # 패널 텍스트 구성
                    text_parts = [
                        f"Dashboard: {title}",
                        f"Panel: {panel_title}",
                        f"Type: {panel_type}",
                    ]
                    if description:
                        text_parts.append(f"Description: {description}")

                    # targets(쿼리) 정보 추가
                    targets = panel.get("targets", [])
                    for t in targets[:3]:
                        expr = t.get("expr") or t.get("query") or t.get("rawSql") or ""
                        if expr:
                            text_parts.append(f"Query: {expr[:300]}")

                    content = "\n".join(text_parts)
                    filename = f"grafana/{uid}/{panel_title}"

                    doc_id = await execute_insert(
                        f"INSERT INTO tbl_grafanadashboard_documents "
                        f"(filename, content, uploaded_by, dashboard_uid, panel_title) "
                        f"VALUES ({_PH},{_PH},{_PH},{_PH},{_PH})",
                        (filename, content, user.get("sub", "sync"), uid, panel_title),
                    )

                    chunks = _chunk_text(content)
                    for idx, chunk in enumerate(chunks):
                        vec = await _embed(chunk)
                        await execute_write(
                            f"INSERT INTO tbl_grafanadashboard_chunks "
                            f"(doc_id, chunk_index, content, embedding_json) "
                            f"VALUES ({_PH},{_PH},{_PH},{_PH})",
                            (doc_id, idx, chunk, json.dumps(vec)),
                        )

                    ingested.append({
                        "doc_id": doc_id,
                        "dashboard_uid": uid,
                        "dashboard_title": title,
                        "panel_title": panel_title,
                    })

            except Exception as e:
                errors.append({"uid": uid, "error": str(e)})

    return {
        "ingested": len(ingested),
        "documents": ingested,
        "errors": errors,
    }


@router.get("/dashboards")
async def list_dashboards(user: dict = Depends(get_current_user)):
    """동기화된 Grafana 대시보드 목록을 반환합니다."""
    rows = await fetch_all(
        "SELECT DISTINCT dashboard_uid, "
        "MAX(filename) AS sample_filename, "
        "COUNT(*) AS panel_count, "
        "MAX(created_at) AS last_synced "
        "FROM tbl_grafanadashboard_documents "
        "WHERE dashboard_uid IS NOT NULL "
        "GROUP BY dashboard_uid "
        "ORDER BY last_synced DESC"
    )
    return {"dashboards": rows, "total": len(rows)}


# ─── 내부 헬퍼 ───────────────────────────────────────────────────────────────

def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """텍스트를 chunk_size 크기로 overlap을 두고 분할합니다."""
    chunks = []
    i = 0
    while i < len(text):
        chunks.append(text[i: i + chunk_size])
        i += chunk_size - overlap
    return chunks
