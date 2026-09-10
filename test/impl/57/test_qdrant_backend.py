"""impl/57 — E7(부분) Qdrant 벡터 백엔드 어댑터 시험. fresh sqlite, 실 TestClient.

전제(mock-first): qdrant-client 미설치(오프라인/폐쇄망 기본). VECTOR_BACKEND=qdrant 여도 resolve()가
'local' 로 우아하게 폴백하고, RAG 인덱싱·검색이 무중단으로 동작해야 한다.
qdrant-client + 실 Qdrant 서버가 갖춰지면 resolve()='qdrant' 경로가 활성화된다(별도 인프라 검증).

실행: .venv/bin/python test/impl/57/test_qdrant_backend.py
"""
import os
import sys
import tempfile

tmp = tempfile.mkdtemp()
os.environ["ENV"] = "local"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-xx"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"
os.environ["AGENT_STANDALONE"] = "1"
os.environ["VECTOR_BACKEND"] = "qdrant"  # qdrant 선택 → client 미설치 시 local 폴백

from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.services import vector_backend as vb  # noqa: E402
import app.main as m  # noqa: E402

AH = {"Authorization": f"Bearer {create_access_token({'sub': 'a1', 'role': 'admin', 'username': 'a1'})}"}
UH = {"Authorization": f"Bearer {create_access_token({'sub': 'u1', 'role': 'user', 'username': 'u1'})}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

try:
    import qdrant_client  # noqa: F401
    HAS_QDRANT = True
except ImportError:
    HAS_QDRANT = False

# ── 유닛: resolve 폴백 ──
chk(settings.vector_backend == "qdrant", "settings.vector_backend=qdrant 반영")
r = vb.resolve()
if HAS_QDRANT:
    chk(r in ("qdrant", "local"), f"resolve qdrant|local ({r})")  # 서버 유무에 따라
else:
    chk(r == "local", f"qdrant-client 미설치 → resolve=local ({r})")

# write_embedding/dense_scores 폴백 무크래시
import asyncio  # noqa: E402
async def _fallback_ops():
    await vb.ensure_pg_schema(256)                      # no-op(local)
    await vb.write_embedding(1, [0.1] * 256, 7)         # no-op(local)
    return await vb.dense_scores(7, [0.1] * 256, 5)     # None(local → 호출측 폴백)
ds = asyncio.run(_fallback_ops())
chk(ds is None or isinstance(ds, dict), f"dense_scores 폴백 안전({type(ds).__name__})")

# ── E2E: qdrant 선택이어도 RAG 무중단(local 폴백) ──
with TestClient(m.app) as c:
    r = c.post("/api/rag/collections", headers=AH, json={"name": "docs", "sensitivity": "general"})
    chk(r.status_code == 201, f"create collection 201 ({r.status_code} {r.text[:120]})")
    cid = r.json()["id"]

    r = c.post(f"/api/rag/collections/{cid}/documents", headers=AH,
               json={"title": "doc-a", "text": "The quick brown fox. SKU-99887 identifies this product."})
    chk(r.status_code == 201 and r.json()["chunks"] >= 1, f"ingest 무중단(qdrant 선택, local 폴백) ({r.json()})")

    r = c.post(f"/api/rag/collections/{cid}/search", headers=AH, json={"query": "SKU-99887"})
    chk(r.status_code == 200, f"search 200 ({r.status_code})")
    hits = r.json()["hits"]
    chk(len(hits) >= 1 and "SKU-99887" in hits[0]["text"], f"검색 결과 무중단 ({len(hits)} hits)")

    r = c.post(f"/api/rag/collections/{cid}/documents", headers=UH, json={"title": "x", "text": "y"})
    chk(r.status_code == 403, "user ingest 403(RBAC 유지)")

print(f"\n=== RESULT: {'PASS' if not fails else 'FAIL'} ({len(fails)} failing) === (qdrant-client installed: {HAS_QDRANT})")
if fails:
    print("FAILED:", fails)
sys.exit(1 if fails else 0)
