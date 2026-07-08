"""router_playground (F-PG) — /api/playground.

프롬프트/모델/RAG 컬렉션 조합 대화형 실험. 공유 LLM 폴백(Ollama)을 실호출하고,
`rag_collection_id` 지정 시 하이브리드 검색 결과를 인용(citations)과 함께 컨텍스트로 주입한다.
미구성/장애 시 degrade 텍스트로 완료(무중단, PRD §7.11.1 준용). 실행 기록으로 A/B 비교를 지원한다.

승격 경로(PRD §7.7): 여기서 검증된 프롬프트/설정은 Workflow `llm` 노드 또는 Marketplace 게시로 이어진다.
"""
import json
import time

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.core.deps import get_current_user
from app.db import _PH, execute_insert, fetch_all, fetch_one
from app.services.llm_fallback import call_ollama
from app.services.rag_pipeline import hybrid_search

router = APIRouter(prefix="/api/playground", tags=["playground"])


def _tenant() -> str:
    return settings.tenant_default_id or "default"


class RunRequest(BaseModel):
    prompt: str = Field(min_length=1)
    system: str = ""
    model: str | None = None
    rag_collection_id: int | None = None
    top_k: int | None = None


@router.post("/run", status_code=201)
async def run(body: RunRequest, user: dict = Depends(get_current_user)):
    tid = _tenant()
    citations: list[dict] = []
    prompt = body.prompt
    system = body.system

    if body.rag_collection_id is not None:
        coll = await fetch_one(
            f"SELECT id, embedding_dim FROM rag_collections WHERE id = {_PH} AND tenant_id = {_PH}",
            (body.rag_collection_id, tid),
        )
        if not coll:
            raise HTTPException(404, "rag_collection_id not found")
        hits = await hybrid_search(coll["id"], coll["embedding_dim"], body.prompt, body.top_k or 3)
        citations = [
            {"chunk_id": h.chunk_id, "document_id": h.document_id, "text": h.text, "rrf_score": h.rrf_score}
            for h in hits
        ]
        if citations:
            context = "\n\n".join(f"[{i + 1}] {c['text']}" for i, c in enumerate(citations))
            prompt = f"다음 컨텍스트를 참고해 답하세요. 인용 시 [번호]를 사용하세요.\n\n{context}\n\n질문: {body.prompt}"

    started = time.monotonic()
    try:
        text = await call_ollama([{"role": "user", "content": prompt}], system=system, model=body.model)
        provider = "ollama"
    except Exception as exc:  # noqa: BLE001 — LLM 미구성/장애 → degrade(무중단)
        text = f"[degraded] {body.prompt}"
        provider = "degraded"
        _ = exc
    latency_ms = int((time.monotonic() - started) * 1000)

    rid = await execute_insert(
        f"INSERT INTO playground_runs "
        f"(tenant_id, prompt, system_prompt, model, rag_collection_id, response_text, provider, latency_ms, citations_json, created_by) "
        f"VALUES ({','.join([_PH] * 10)})",
        (tid, body.prompt, system, body.model or settings.ollama_model, body.rag_collection_id,
         text, provider, latency_ms, json.dumps(citations, ensure_ascii=False),
         user.get("username") or user.get("sub") or ""),
    )
    return await fetch_one("SELECT * FROM playground_runs WHERE id = " + _PH, (rid,))


@router.get("/runs")
async def list_runs(limit: int = 50, user: dict = Depends(get_current_user)):
    rows = await fetch_all(
        f"SELECT * FROM playground_runs WHERE tenant_id = {_PH} ORDER BY id DESC LIMIT {_PH}",
        (_tenant(), min(limit, 200)),
    )
    return {"runs": rows}
