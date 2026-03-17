"""
ChromaDB service — vector embeddings for document RAG.
"""
from __future__ import annotations
from typing import Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from app.config import settings

# Use Optional[object] — chromadb.HttpClient is a factory function, not a type
_client: Optional[object] = None
COLLECTION_NAME = "intellicredit_docs"


def get_chroma():
    global _client
    if _client is None:
        _client = chromadb.HttpClient(
            host=settings.chroma_host,
            port=int(settings.chroma_port),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
    return _client


def get_collection():
    client = get_chroma()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def upsert_chunks(
    app_id: str,
    doc_type: str,
    source_filename: str,
    chunks: list[dict],        # [{text, page_number, chunk_id}]
    embeddings: Optional[list] = None,  # None → chromadb uses its default embedder
):
    """
    Store document chunks in ChromaDB.
    If embeddings=None, chromadb's built-in embedding function is used automatically.
    """
    if not chunks:
        return

    collection = get_collection()
    ids = [f"{app_id}_{source_filename}_{c['chunk_id']}" for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [
        {
            "app_id": app_id,
            "doc_type": doc_type,
            "source": source_filename,
            "page_number": str(c.get("page_number", 0)),  # chroma needs strings
        }
        for c in chunks
    ]

    if embeddings is not None:
        collection.upsert(ids=ids, documents=documents,
                          embeddings=embeddings, metadatas=metadatas)
    else:
        # Let chromadb embed automatically
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


def query_documents(app_id: str, query_text: str, n_results: int = 5) -> list[dict]:
    """Semantic search within a single application's documents."""
    try:
        collection = get_collection()
        results = collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where={"app_id": app_id},
        )
        return [
            {"text": doc, "metadata": meta, "distance": dist}
            for doc, meta, dist in zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0],
            )
        ]
    except Exception:
        return []




