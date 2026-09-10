"""RAG 파이프라인 (F-RAG) — 청킹→임베딩→인덱싱 + 하이브리드 검색(BM25+dense+RRF).

pgvector 기본은 확장(PRD §7.5); 로컬(SQLite)은 임베딩 JSON + 파이썬 코사인/BM25.
융합: RRF(k=60). 식별자성 질의는 sparse(BM25) 경로가 Recall 을 견인.

참조: SeCuardian-Marketplace-v0 rag_pipeline 을 async raw-SQL 로 이식.
"""
import json
import math
from dataclasses import dataclass

from app.core.config import settings
from app.db import _PH, execute_insert, fetch_all
from app.services.embeddings import cosine, embed, term_freq, tokenize


def chunk_text(text: str, size: int = 400, overlap: int = 40) -> list[str]:
    """단순 문자 기반 청킹(overlap 포함). 문서유형별 정책은 로드맵."""
    text = (text or "").strip()
    if not text:
        return []
    if len(text) <= size:
        return [text]
    chunks, start = [], 0
    while start < len(text):
        chunks.append(text[start : start + size])
        start += size - overlap
    return chunks


async def index_document(tenant_id: str, collection_id: int, embedding_dim: int, document_id: int, text: str) -> int:
    """문서를 청킹·임베딩·인덱싱. 생성된 청크 수 반환.

    pgvector 백엔드 활성 시(§7.5) vector 컬럼에도 임베딩을 기록(로컬은 embedding_json 만).
    """
    from app.services import vector_backend
    await vector_backend.ensure_pg_schema(embedding_dim)
    pieces = chunk_text(text)
    for ordinal, piece in enumerate(pieces):
        vec = embed(piece, embedding_dim)
        tf = term_freq(piece)
        cid = await execute_insert(
            f"INSERT INTO rag_chunks "
            f"(tenant_id, collection_id, document_id, ordinal, text, embedding_json, terms_json, token_count, norm) "
            f"VALUES ({','.join([_PH] * 9)})",
            (tenant_id, collection_id, document_id, ordinal, piece,
             json.dumps(vec), json.dumps(tf, ensure_ascii=False), sum(tf.values()), 1.0),
        )
        await vector_backend.write_embedding(cid, vec, collection_id)
    return len(pieces)


@dataclass
class SearchHit:
    chunk_id: int
    document_id: int
    text: str
    dense_rank: int | None
    bm25_rank: int | None
    dense_score: float
    bm25_score: float
    rrf_score: float


def _bm25_scores(query: str, chunks: list[dict]) -> dict[int, float]:
    """표준 BM25(k1=1.5, b=0.75), 코퍼스=컬렉션 청크."""
    q_terms = set(tokenize(query))
    if not q_terms or not chunks:
        return {}
    n = len(chunks)
    tfs = {c["id"]: json.loads(c.get("terms_json") or "{}") for c in chunks}
    lengths = {cid: sum(tf.values()) or 1 for cid, tf in tfs.items()}
    avgdl = sum(lengths.values()) / n
    df: dict[str, int] = {}
    for tf in tfs.values():
        for term in q_terms:
            if term in tf:
                df[term] = df.get(term, 0) + 1
    k1, b = 1.5, 0.75
    scores: dict[int, float] = {}
    for cid, tf in tfs.items():
        s = 0.0
        for term in q_terms:
            f = tf.get(term, 0)
            if f == 0:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            s += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * lengths[cid] / avgdl))
        if s > 0:
            scores[cid] = s
    return scores


async def hybrid_search(collection_id: int, embedding_dim: int, query: str, top_k: int | None = None) -> list[SearchHit]:
    top_k = top_k or settings.rag_default_top_k
    chunks = await fetch_all(
        f"SELECT id, document_id, text, embedding_json, terms_json FROM rag_chunks WHERE collection_id = {_PH}",
        (collection_id,),
    )
    if not chunks:
        return []
    by_id = {c["id"]: c for c in chunks}

    # dense — pgvector 백엔드 활성 시 SQL ANN, 아니면 파이썬 코사인 폴백(§7.5)
    from app.services import vector_backend
    q_vec = embed(query, embedding_dim)
    dense = await vector_backend.dense_scores(collection_id, q_vec, top_k)
    if dense is None:
        dense = {c["id"]: cosine(q_vec, json.loads(c.get("embedding_json") or "[]")) for c in chunks}
        dense = {cid: s for cid, s in dense.items() if s > 0}

    # sparse
    bm25 = _bm25_scores(query, chunks)

    dense_ranked = sorted(dense, key=lambda cid: dense[cid], reverse=True)
    bm25_ranked = sorted(bm25, key=lambda cid: bm25[cid], reverse=True)
    dense_rank = {cid: i + 1 for i, cid in enumerate(dense_ranked)}
    bm25_rank = {cid: i + 1 for i, cid in enumerate(bm25_ranked)}

    # RRF 융합
    k = settings.rag_rrf_k
    candidates = set(dense_rank) | set(bm25_rank)
    hits = []
    for cid in candidates:
        rrf = 0.0
        if cid in dense_rank:
            rrf += 1.0 / (k + dense_rank[cid])
        if cid in bm25_rank:
            rrf += 1.0 / (k + bm25_rank[cid])
        c = by_id[cid]
        hits.append(
            SearchHit(
                chunk_id=cid,
                document_id=c["document_id"],
                text=c["text"],
                dense_rank=dense_rank.get(cid),
                bm25_rank=bm25_rank.get(cid),
                dense_score=round(dense.get(cid, 0.0), 6),
                bm25_score=round(bm25.get(cid, 0.0), 6),
                rrf_score=round(rrf, 6),
            )
        )
    hits.sort(key=lambda h: h.rrf_score, reverse=True)
    return hits[:top_k]
