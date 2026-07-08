"""F-RAG pgvector 어댑터 test — 백엔드 리졸버 + sqlite 폴백(로컬 하이브리드검색 불변) 검증.

pgvector 실동작은 PostgreSQL + CREATE EXTENSION vector 필요(이 세션 sqlite) → resolve()='local' 폴백
경로만 검증(사용자 승인 시 인지된 제약). pgvector 라이브러리 설치·경로 코드 무결성은 import/정적으로 확인.
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
os.environ["VECTOR_BACKEND"] = "pgvector"   # 요청은 pgvector 지만 sqlite → local 폴백돼야 함

import asyncio  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
import app.main as m  # noqa: E402
from app.services import vector_backend  # noqa: E402

H = {"Authorization": f"Bearer {create_access_token({'sub':'sup1','role':'supervisor','username':'sup1'})}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

# 1) pgvector 라이브러리 설치 확인
try:
    import pgvector  # noqa: F401
    chk(True, "pgvector 라이브러리 import OK")
except Exception as e:
    chk(False, f"pgvector import 실패: {e}")

# 2) VECTOR_BACKEND=pgvector + sqlite → resolve()='local' (폴백)
chk(vector_backend.resolve() == "local", f"sqlite → local 폴백 ({vector_backend.resolve()})")

# 3) local 에서 pg 전용 헬퍼는 no-op/None (무중단)
asyncio.run(vector_backend.ensure_pg_schema(256))   # no-op, 예외 없어야
asyncio.run(vector_backend.write_embedding(1, [0.1] * 256))  # no-op
r = asyncio.run(vector_backend.dense_scores(1, [0.1] * 256, 10))
chk(r is None, f"local dense_scores → None(폴백 신호) ({r})")

# 4) 통합: sqlite 로컬 하이브리드검색 여전히 정상(식별자 질의 BM25 최상위)
with TestClient(m.app) as c:
    cid = c.post("/api/rag/collections", headers=H, json={"name": "kb"}).json()["id"]
    c.post(f"/api/rag/collections/{cid}/documents", headers=H,
           json={"title": "d", "text": "SKU-77821 identifies this widget."})
    c.post(f"/api/rag/collections/{cid}/documents", headers=H,
           json={"title": "e", "text": "unrelated weather report about clouds."})
    r = c.post(f"/api/rag/collections/{cid}/search", headers=H, json={"query": "SKU-77821"})
    hits = r.json()["hits"]
    chk(r.status_code == 200 and hits and hits[0]["bm25_rank"] == 1, f"로컬 하이브리드검색 정상(BM25 top) ({hits[:1]})")
    chk("SKU-77821" in hits[0]["text"], "top hit = 식별자 문서")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
