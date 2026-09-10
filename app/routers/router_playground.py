"""router_playground (F-PG) — /api/playground.

프롬프트/모델/RAG 컬렉션 조합 대화형 실험. 공유 LLM 폴백(Ollama)을 실호출하고,
`rag_collection_id` 지정 시 하이브리드 검색 결과를 인용(citations)과 함께 컨텍스트로 주입한다.
미구성/장애 시 degrade 텍스트로 완료(무중단, PRD §7.11.1 준용). 실행 기록으로 A/B 비교를 지원한다.

승격 경로(PRD §7.7): 여기서 검증된 프롬프트/설정은 Workflow `llm` 노드 또는 Marketplace 게시로 이어진다.
"""
import json
import os
import re
import time
from typing import Optional

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
    usage: dict = {}  # call_ollama 가 prompt_eval_count/eval_count 를 누적(관측성, §7.9)
    try:
        text = await call_ollama([{"role": "user", "content": prompt}], system=system, model=body.model, usage_out=usage)
        provider = "ollama"
    except Exception as exc:  # noqa: BLE001 — LLM 미구성/장애 → degrade(무중단)
        text = f"[degraded] {body.prompt}"
        provider = "degraded"
        _ = exc
    latency_ms = int((time.monotonic() - started) * 1000)
    in_tok = int(usage.get("input_tokens", 0))
    out_tok = int(usage.get("output_tokens", 0))

    rid = await execute_insert(
        f"INSERT INTO playground_runs "
        f"(tenant_id, prompt, system_prompt, model, rag_collection_id, response_text, provider, latency_ms, "
        f"input_tokens, output_tokens, citations_json, created_by) "
        f"VALUES ({','.join([_PH] * 12)})",
        (tid, body.prompt, system, body.model or settings.ollama_model, body.rag_collection_id,
         text, provider, latency_ms, in_tok, out_tok, json.dumps(citations, ensure_ascii=False),
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


# ─── 비용 추적 (E12/impl/56) — playground_runs 토큰 집계 × 모델 단가 ─────────────

# 기본 단가 (USD / 1K 토큰) — PG_COST_RATES(JSON) 로 오버라이드. degraded 는 무료.
_DEFAULT_RATES = {
    "default": {"input": 0.0, "output": 0.0},  # 로컬 Ollama — 무료
    "claude-opus-4-8": {"input": 0.015, "output": 0.075},
    "claude-sonnet-5": {"input": 0.003, "output": 0.015},
    "claude-haiku-4-5": {"input": 0.0008, "output": 0.004},
}


def _rates() -> dict:
    raw = os.getenv("PG_COST_RATES", "").strip()
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return {**_DEFAULT_RATES, **data}
        except ValueError:
            pass
    return _DEFAULT_RATES


def _rate_for(model: str, provider: str, rates: dict) -> dict:
    if provider == "degraded":
        return {"input": 0.0, "output": 0.0}
    return rates.get(model) or rates["default"]


@router.get("/cost")
async def cost_summary(user: dict = Depends(get_current_user)):
    """playground_runs 토큰 사용량을 모델 단가로 환산한 비용 요약(모델별 + 총계)."""
    rows = await fetch_all(
        f"SELECT model, provider, COALESCE(SUM(input_tokens),0) AS i, COALESCE(SUM(output_tokens),0) AS o, "
        f"COUNT(*) AS runs FROM playground_runs WHERE tenant_id = {_PH} GROUP BY model, provider",
        (_tenant(),))
    rates = _rates()
    by_model = []
    total_cost = 0.0
    total_in = total_out = total_runs = 0
    for r in rows:
        model = r.get("model") or "default"
        provider = r.get("provider") or ""
        rt = _rate_for(model, provider, rates)
        i, o, runs = int(r.get("i", 0)), int(r.get("o", 0)), int(r.get("runs", 0))
        cost = round(i / 1000 * rt["input"] + o / 1000 * rt["output"], 6)
        total_cost += cost
        total_in += i
        total_out += o
        total_runs += runs
        by_model.append({"model": model, "provider": provider, "runs": runs,
                         "input_tokens": i, "output_tokens": o, "cost_usd": cost, "rate": rt})
    return {
        "by_model": by_model,
        "totals": {"runs": total_runs, "input_tokens": total_in, "output_tokens": total_out,
                   "cost_usd": round(total_cost, 6)},
        "currency": "USD", "unit": "per 1K tokens", "note": "degraded(로컬 Ollama)=무료",
    }


# ─── Eval 실행 (E12/impl/56) — run 출력 vs assertions 평가 ─────────────────────

class Assertion(BaseModel):
    type: str            # contains | not_contains | regex | equals | min_length
    value: str = ""


class EvalRequest(BaseModel):
    assertions: list[Assertion]
    run_id: Optional[int] = None
    output: Optional[str] = None


def _eval_one(a: Assertion, text: str) -> dict:
    t = a.type.strip().lower()
    val = a.value or ""
    if t == "contains":
        ok = val in text
    elif t == "not_contains":
        ok = val not in text
    elif t == "equals":
        ok = text.strip() == val.strip()
    elif t == "min_length":
        try:
            ok = len(text) >= int(val)
        except ValueError:
            ok = False
    elif t == "regex":
        try:
            ok = re.search(val, text) is not None
        except re.error:
            raise HTTPException(status_code=422, detail=f"잘못된 정규식: {val!r}")
    else:
        raise HTTPException(status_code=422, detail=f"지원하지 않는 assertion type: {a.type!r}")
    return {"type": t, "value": val[:200], "passed": ok}


@router.post("/eval")
async def run_eval(body: EvalRequest, user: dict = Depends(get_current_user)):
    """run 출력(run_id 조회 또는 output 직접)을 assertions 로 평가한다."""
    if not body.assertions:
        raise HTTPException(status_code=422, detail="assertions 가 비어있습니다.")
    if body.run_id is not None:
        row = await fetch_one(
            f"SELECT response_text FROM playground_runs WHERE tenant_id = {_PH} AND id = {_PH}",
            (_tenant(), body.run_id))
        if not row:
            raise HTTPException(status_code=404, detail="run 없음")
        text = row.get("response_text") or ""
    elif body.output is not None:
        text = body.output
    else:
        raise HTTPException(status_code=422, detail="run_id 또는 output 중 하나가 필요합니다.")

    results = [_eval_one(a, text) for a in body.assertions]
    passed = sum(1 for r in results if r["passed"])
    return {
        "results": results,
        "score": {"passed": passed, "total": len(results),
                  "pass_rate": round(passed / len(results), 3), "all_passed": passed == len(results)},
        "source": "run_id" if body.run_id is not None else "output",
    }
