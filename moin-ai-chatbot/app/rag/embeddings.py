"""
Embedding generation. Kept as a thin, swappable adapter (mirrors the
provider-adapter pattern used for the chat LLM in app/llm/) so switching
embedding providers later doesn't touch the ingestion or retrieval logic.

Provider: Gemini (`gemini-embedding-001`), 768 output dimensions (Matryoshka
truncation of the native 3072-dim output — see SRS/config for the rationale).

Note: gemini-embedding-001 does NOT auto-normalize truncated (<3072-dim)
output the way newer Gemini embedding models do, so we normalize manually
per Google's documented guidance — skipping this silently degrades cosine
similarity search quality.
"""
import numpy as np
from google import genai
from google.genai import types

from app.core.config import get_settings

settings = get_settings()
_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Embeddings require a Gemini API key "
                "(https://aistudio.google.com/apikey)."
            )
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _normalize(vector: list[float]) -> list[float]:
    arr = np.array(vector, dtype=np.float32)
    norm = np.linalg.norm(arr)
    if norm == 0:
        return vector
    return (arr / norm).tolist()


def embed_texts(
    texts: list[str],
    batch_size: int = 20,
    task_type: str = "RETRIEVAL_DOCUMENT",
) -> list[list[float]]:
    """Embed a list of texts, preserving input order. Batches to stay well
    under the API's per-request limits and free-tier rate limits.

    task_type: "RETRIEVAL_DOCUMENT" for knowledge-base ingestion (default),
    "RETRIEVAL_QUERY" for embedding an incoming user question at retrieval
    time — keep this consistent with how the corresponding side was embedded.
    """
    client = _get_client()
    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.models.embed_content(
            model=settings.embedding_model,
            contents=batch,
            config=types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=settings.embedding_dimensions,
            ),
        )
        # API returns results in the same order as the input list
        all_embeddings.extend(_normalize(item.values) for item in response.embeddings)
    return all_embeddings


def embed_query(text: str) -> list[float]:
    """Convenience wrapper for embedding a single user query at retrieval
    time (Day 3) — uses RETRIEVAL_QUERY task type to match the asymmetric
    document/query embedding scheme used for the knowledge base."""
    return embed_texts([text], batch_size=1, task_type="RETRIEVAL_QUERY")[0]
