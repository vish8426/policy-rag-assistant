"""Persistent Chroma vector store: build and query.

We compute embeddings ourselves (see ``embedder.py``) and hand Chroma the vectors,
so the store is independent of Chroma's default embedding function and fully
deterministic. Cosine distance is used to match the normalized embeddings.
"""
from __future__ import annotations

from typing import List

import chromadb

from .chunker import Chunk
from .embedder import Embedder


def _client(chroma_dir: str):
    return chromadb.PersistentClient(path=chroma_dir)


def build_index(
    chunks: List[Chunk],
    embedder: Embedder,
    chroma_dir: str,
    collection_name: str,
    reset: bool = True,
    batch_size: int = 64,
) -> int:
    """Embed chunks and (re)build the Chroma collection. Returns the chunk count."""
    client = _client(chroma_dir)

    if reset:
        try:
            client.delete_collection(collection_name)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"},
    )

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        embeddings = embedder.embed([c.text for c in batch])
        collection.add(
            ids=[c.id for c in batch],
            embeddings=embeddings,
            documents=[c.text for c in batch],
            metadatas=[c.metadata for c in batch],
        )
    return collection.count()


def get_collection(chroma_dir: str, collection_name: str):
    """Open an existing collection for querying (used by the RAG retriever in Stage 3)."""
    return _client(chroma_dir).get_collection(collection_name)


def query(
    collection,
    embedder: Embedder,
    text: str,
    k: int,
):
    """Convenience top-k query returning Chroma's result dict."""
    q_emb = embedder.embed([text])
    return collection.query(
        query_embeddings=q_emb,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
