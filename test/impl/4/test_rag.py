"""F-RAG functional test — fresh sqlite, TestClient. Collections, ingest, hybrid search, RBAC."""
import os
import sys
import tempfile

tmp = tempfile.mkdtemp()
os.environ["ENV"] = "local"
os.environ["DATABASE_URL"] = f"sqlite:///{tmp}/t.db"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-32-characters-min-xx"
os.environ["OLLAMA_WARMUP_ENABLED"] = "false"
os.environ["AGENT_STANDALONE"] = "1"

from fastapi.testclient import TestClient  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
import app.main as m  # noqa: E402

TOK = create_access_token({"sub": "sup1", "role": "supervisor", "username": "sup1"})
H = {"Authorization": f"Bearer {TOK}"}
UTOK = create_access_token({"sub": "u1", "role": "user", "username": "u1"})
UH = {"Authorization": f"Bearer {UTOK}"}

fails = []
def chk(cond, msg):
    print(("PASS" if cond else "FAIL"), msg)
    if not cond:
        fails.append(msg)

with TestClient(m.app) as c:
    r = c.get("/api/agent-config/", headers=H)
    keys = [a["agent_key"] for a in (r.json() if isinstance(r.json(), list) else r.json().get("agents", []))]
    chk("rag" in keys, f"rag agent seeded ({keys})")

    # RBAC
    r = c.post("/api/rag/collections", headers=UH, json={"name": "x"})
    chk(r.status_code == 403, "user create collection -> 403")

    # bad sensitivity
    r = c.post("/api/rag/collections", headers=H, json={"name": "bad", "sensitivity": "public"})
    chk(r.status_code == 422, "bad sensitivity -> 422")

    # create collection
    r = c.post("/api/rag/collections", headers=H, json={"name": "docs", "sensitivity": "general"})
    chk(r.status_code == 201, f"create collection 201 ({r.status_code})")
    cid = r.json()["id"]
    chk(r.json()["embedding_dim"] == 256, "embedding_dim default 256")

    # duplicate name
    r = c.post("/api/rag/collections", headers=H, json={"name": "docs"})
    chk(r.status_code == 409, "duplicate collection name -> 409")

    # ingest documents (distinct identifier terms for BM25 signal)
    r = c.post(f"/api/rag/collections/{cid}/documents", headers=H, json={
        "title": "doc-a", "text": "The quick brown fox jumps over the lazy dog. SKU-12345 identifies this product."
    })
    chk(r.status_code == 201 and r.json()["chunks"] >= 1, f"ingest doc-a ({r.json()})")
    r = c.post(f"/api/rag/collections/{cid}/documents", headers=H, json={
        "title": "doc-b", "text": "Completely unrelated content about weather and clouds and rain forecast today."
    })
    chk(r.status_code == 201, "ingest doc-b")

    # user can ingest? no -> 403
    r = c.post(f"/api/rag/collections/{cid}/documents", headers=UH, json={"title": "x", "text": "y"})
    chk(r.status_code == 403, "user ingest -> 403")

    # list documents
    r = c.get(f"/api/rag/collections/{cid}/documents", headers=H)
    chk(r.status_code == 200 and len(r.json()["documents"]) == 2, f"list documents = 2 ({r.json()})")

    # search: identifier term (SKU-12345) should surface doc-a via BM25
    r = c.post(f"/api/rag/collections/{cid}/search", headers=H, json={"query": "SKU-12345"})
    chk(r.status_code == 200, "search 200")
    hits = r.json()["hits"]
    chk(len(hits) >= 1, f"search returns hits ({len(hits)})")
    chk(hits[0]["bm25_rank"] == 1, f"top hit has bm25_rank=1 ({hits[0]})")
    chk("SKU-12345" in hits[0]["text"], f"top hit is the SKU doc ({hits[0]['text'][:60]})")

    # search on unrelated collection -> 404
    r = c.post("/api/rag/collections/99999/search", headers=H, json={"query": "x"})
    chk(r.status_code == 404, "search on missing collection -> 404")

    # unauth
    chk(c.get("/api/rag/collections").status_code in (401, 403), "no token -> 401/403")

print("\n=== RESULT:", "ALL PASS" if not fails else f"{len(fails)} FAIL: {fails}")
sys.exit(1 if fails else 0)
