"""
Vector similarity retrieval over knowledge_chunk (SRS section 13-14).

Deliberately simple for Day 3: pure cosine-similarity search across all
chunks, no metadata/intent filtering yet — that's layered on later once
intent detection exists (SRS 14: "use metadata filtering when
intent/category is known").

Two-step design mirrors the SRS retrieval flow diagram: retrieve() does
the ranked top-k lookup with no cutoff (so evaluation can measure raw
ranking quality), and apply_threshold() is a separate step the chat
orchestration layer will use to decide whether context is confident
enough to answer from, or fall back to the unknown-answer policy.
"""
import logging
from dataclasses import dataclass

from sqlalchemy import select

from app.core.config import get_settings
from app.db.models import KnowledgeChunk
from app.db.session import db_session
from app.rag.embeddings import embed_query

settings = get_settings()
logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    record_id: str
    title: str | None
    content: str
    category: str | None
    intents: list[str] | None
    similarity: float  # cosine similarity, 1.0 = identical, 0.0 = unrelated


def retrieve(query: str, top_k: int | None = None) -> list[RetrievedChunk]:
    """Embed the query and return the top-k most similar knowledge chunks,
    ranked by cosine similarity, highest first. No threshold cutoff applied
    here — see apply_threshold()."""
    top_k = top_k or settings.rag_top_k
    query_vector = embed_query(query)

    results: list[RetrievedChunk] = []
    with db_session() as db:
        # cosine_distance = 1 - cosine_similarity; pgvector's <=> operator
        # via pgvector-python's SQLAlchemy comparator.
        distance = KnowledgeChunk.embedding.cosine_distance(query_vector)
        similarity = (1 - distance).label("similarity")
        stmt = select(KnowledgeChunk, similarity).order_by(distance).limit(top_k)

        for chunk, sim in db.execute(stmt).all():
            results.append(
                RetrievedChunk(
                    record_id=chunk.record_id,
                    title=chunk.title,
                    content=chunk.content,
                    category=chunk.category,
                    intents=chunk.intents,
                    similarity=float(sim),
                )
            )

    logger.debug(
        "retrieval query=%r top_k=%d results=%s",
        query,
        top_k,
        [(r.record_id, round(r.similarity, 4)) for r in results],
    )
    return results


def apply_threshold(
    results: list[RetrievedChunk], threshold: float | None = None
) -> list[RetrievedChunk]:
    """Filter ranked results down to only those confident enough to ground
    an answer on. Empty result = the unknown-answer policy should kick in
    (SRS 14: 'if no adequate context is retrieved, use the unknown-answer
    policy instead of hallucinating')."""
    threshold = threshold if threshold is not None else settings.rag_similarity_threshold
    return [r for r in results if r.similarity >= threshold]
