"""
ChromaDB service — vector embeddings for document RAG.
Gracefully disabled when chromadb is not installed (hackathon mode).
"""
from __future__ import annotations
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False
    logger.info("chromadb not installed — vector search disabled")

from app.config import settings

_client: Optional[object] = None


def get_chroma():
    if not _CHROMA_AVAILABLE:
        return None
    global _client
    if _client is None:
        try:
            _client = chromadb.HttpClient(
                host=settings.chroma_host,
                port=int(settings.chroma_port),
                settings=ChromaSettings(anonymized_telemetry=False),
            )
        except Exception as e:
            logger.warning("ChromaDB connection failed: %s", e)
            return None
    return _client


def upsert_chunks(app_id: str, doc_type: str, source_filename: str,
                  chunks: list[dict], embeddings=None):
    """Store document chunks. No-op if chromadb unavailable."""
    if not _CHROMA_AVAILABLE or not chunks:
        return
    try:
        client = get_chroma()
        if not client:
            return
        collection = client.get_or_create_collection(
            name="intellicredit_docs",
            metadata={"hnsw:space": "cosine"},
        )
        ids = [f"{app_id}_{source_filename}_{c['chunk_id']}" for c in chunks]
        metadatas = [{"app_id": app_id, "doc_type": doc_type,
                      "source": source_filename, "page_number": str(c.get("page_number", 0))}
                     for c in chunks]
        collection.upsert(ids=ids, documents=[c["text"] for c in chunks], metadatas=metadatas)
    except Exception as e:
        logger.debug("ChromaDB upsert failed: %s", e)


def query_documents(app_id: str, query_text: str, n_results: int = 5) -> list[dict]:
    """Semantic search. Returns empty list if chromadb unavailable."""
    if not _CHROMA_AVAILABLE:
        return []
    try:
        client = get_chroma()
        if not client:
            return []
        collection = client.get_or_create_collection("intellicredit_docs")
        results = collection.query(query_texts=[query_text], n_results=n_results,
                                   where={"app_id": app_id})
        return [{"text": doc, "metadata": meta, "distance": dist}
                for doc, meta, dist in zip(results["documents"][0],
                                           results["metadatas"][0],
                                           results["distances"][0])]
    except Exception:
        return []
