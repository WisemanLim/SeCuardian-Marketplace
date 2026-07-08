"""로컬 임베더 (F-RAG) — 폐쇄망/오프라인 기본.

해싱 트릭 기반 결정적 임베딩(외부 모델·네트워크 불필요). 인터페이스는 실제
임베딩 모델(sentence-transformers/OpenAI 등)로 교체 가능하게 유지(embedding_version 고정).
"""
import hashlib
import math
import re

_TOKEN_RE = re.compile(r"[0-9A-Za-z가-힣_./-]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


def term_freq(text: str) -> dict[str, int]:
    freq: dict[str, int] = {}
    for tok in tokenize(text):
        freq[tok] = freq.get(tok, 0) + 1
    return freq


def _bucket(token: str, dim: int) -> tuple[int, float]:
    h = hashlib.md5(token.encode("utf-8")).digest()
    idx = int.from_bytes(h[:4], "big") % dim
    sign = 1.0 if h[4] & 1 else -1.0
    return idx, sign


def embed(text: str, dim: int = 256) -> list[float]:
    """feature hashing → L2 정규화 dense 벡터."""
    vec = [0.0] * dim
    for tok, cnt in term_freq(text).items():
        idx, sign = _bucket(tok, dim)
        vec[idx] += sign * (1.0 + math.log(cnt))
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 0:
        vec = [v / norm for v in vec]
    return vec


def cosine(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    return sum(x * y for x, y in zip(a, b))  # 둘 다 L2 정규화됨 → 내적 = 코사인
