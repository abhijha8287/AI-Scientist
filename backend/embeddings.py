import numpy as np
import os
from openai import OpenAI

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), timeout=30)
    return _client


EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")


def embed(text: str) -> np.ndarray:
    client = _get_client()
    resp = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000],
    )
    return np.array(resp.data[0].embedding, dtype=np.float32)


def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def novelty_score(hypothesis_text: str, chunk_embeddings: list[np.ndarray]) -> float:
    if not chunk_embeddings:
        return 1.0
    hyp_emb = embed(hypothesis_text)
    sims = [cosine_sim(hyp_emb, ce) for ce in chunk_embeddings]
    return round(1.0 - max(sims), 3)


def serialize_embedding(emb: np.ndarray) -> bytes:
    return emb.tobytes()


def deserialize_embedding(data: bytes) -> np.ndarray:
    return np.frombuffer(data, dtype=np.float32).copy()
