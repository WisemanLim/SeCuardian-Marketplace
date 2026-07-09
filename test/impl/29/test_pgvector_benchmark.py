"""F-RAG pgvector 실측 벤치마크 (impl/31, PRD §7.5.1). 실 PostgreSQL+pgvector 필요.

사전조건: `docker compose up -d postgres` (pgvector/pgvector:pg17 이미지) 로 기동돼 있어야 함.
sqlite 세션이 아니라 실제 Postgres 커넥션을 사용 — 기존 test/impl/* 와 달리 fresh tempfile DB 를
새로 만들지 않고, 벤치마크 전용 스키마를 실 DB 위에 적용한다(멱등, DROP 없이 재실행 가능).
"""
import statistics
import sys
import time

import os
os.environ.setdefault("ENV", "dev")
os.environ.setdefault("DATABASE_URL", "postgresql://app:app@localhost:5432/app")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-32-characters-min-xx")
os.environ.setdefault("OLLAMA_WARMUP_ENABLED", "false")
os.environ.setdefault("AGENT_STANDALONE", "1")
os.environ.setdefault("VECTOR_BACKEND", "pgvector")

from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.services import vector_backend  # noqa: E402
from app.db import fetch_one  # noqa: E402
import app.main as m  # noqa: E402

TOK = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {TOK}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

N_DOCS = 40
FILLER = (
    "This internal knowledge base entry documents an inventory record for warehouse tracking. "
    "It contains routine operational notes unrelated to the identifier lookup itself."
)

with TestClient(m.app) as c:
    chk(vector_backend.resolve() == "pgvector", f"vector_backend.resolve() == pgvector ({vector_backend.resolve()})")

    r = c.post("/api/rag/collections", headers=H, json={"name": f"bench-{int(time.time())}", "sensitivity": "general"})
    chk(r.status_code == 201, f"create collection ({r.status_code}, {r.text[:200]})")
    cid = r.json()["id"]

    ids = [f"SKU-{90000 + i}" for i in range(N_DOCS)]
    for i, sku in enumerate(ids):
        r = c.post(
            f"/api/rag/collections/{cid}/documents", headers=H,
            json={"title": f"doc-{i}", "text": f"{sku} identifies this inventory item. {FILLER}"},
        )
        chk(r.status_code == 201, f"ingest doc {i} ({r.status_code})") if r.status_code != 201 else None

    import asyncio
    row = asyncio.run(fetch_one(
        "SELECT COUNT(*) AS n FROM rag_chunks WHERE collection_id = %s AND embedding IS NOT NULL",
        (cid,),
    ))
    chk(row and row["n"] == N_DOCS, f"pgvector embedding column populated for all chunks ({row})")

    hits_top10 = 0
    latencies_ms = []
    for sku in ids:
        t0 = time.perf_counter()
        r = c.post(f"/api/rag/collections/{cid}/search", headers=H, json={"query": sku, "top_k": 10})
        latencies_ms.append((time.perf_counter() - t0) * 1000)
        if r.status_code == 200:
            texts = [h.get("text", "") for h in r.json().get("hits", [])]
            if any(sku in t for t in texts):
                hits_top10 += 1

    recall_at_10 = hits_top10 / N_DOCS
    latencies_ms.sort()
    p95_idx = max(0, int(len(latencies_ms) * 0.95) - 1)
    p95_ms = latencies_ms[p95_idx]
    p50_ms = statistics.median(latencies_ms)

    print(f"\n--- 실측 결과 (N={N_DOCS}) ---")
    print(f"Recall@10 (identifier queries): {recall_at_10:.3f}  (목표 §5: >=0.89)")
    print(f"p50 latency: {p50_ms:.1f}ms  p95 latency: {p95_ms:.1f}ms  (목표 §5: p95<=250ms)")
    chk(recall_at_10 >= 0.89, f"Recall@10 target met ({recall_at_10:.3f})")
    chk(p95_ms <= 250, f"p95 latency target met ({p95_ms:.1f}ms)")

    # infra-correctness gate: 인프라 자체는 정상 동작해야 함(수치 목표 미달과 별개)
    chk(hits_top10 > 0, f"pgvector search path returns non-trivial results ({hits_top10}/{N_DOCS})")

    r = c.post(f"/api/rag/collections/{cid}/search", headers=H, json={"query": "nonexistent-zzz-000", "top_k": 10})
    chk(r.status_code == 200, f"search with no match still 200 (no crash) ({r.status_code})")

print("\n=== BENCHMARK SUMMARY ===")
print(f"Recall@10={recall_at_10:.3f} p50={p50_ms:.1f}ms p95={p95_ms:.1f}ms N={N_DOCS}")
print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
