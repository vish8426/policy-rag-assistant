"""End-to-end ingestion: load corpus -> chunk -> embed -> store in Chroma."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import config

from .chunker import Chunk, chunk_documents
from .embedder import Embedder, get_embedder
from .loaders import Document, load_corpus


def load_and_chunk(corpus_dir, count_tokens):
    docs = load_corpus(corpus_dir)
    chunks = chunk_documents(docs, count_tokens=count_tokens,
                             max_tokens=config.CHUNK_SIZE_TOKENS,
                             overlap_tokens=config.CHUNK_OVERLAP_TOKENS)
    return docs, chunks


def run(backend="st", corpus_dir=None, dry_run=False):
    """Run ingestion. With dry_run=True, parse + chunk only (no embedding/storage)."""
    config.set_seeds()
    corpus_dir = corpus_dir or config.CORPUS_DIR

    embedder = None
    if dry_run:
        count_tokens = get_embedder("hash", config.EMBEDDING_MODEL, config.EMBEDDING_DIM).count_tokens
    else:
        embedder = get_embedder(backend, config.EMBEDDING_MODEL, config.EMBEDDING_DIM)
        count_tokens = embedder.count_tokens

    docs, chunks = load_and_chunk(corpus_dir, count_tokens)

    stats = {"documents": len(docs), "chunks": len(chunks), "by_format": {},
             "stored": 0, "collection": config.CHROMA_COLLECTION,
             "chroma_dir": config.CHROMA_DIR}
    for d in docs:
        stats["by_format"][d.fmt] = stats["by_format"].get(d.fmt, 0) + 1

    if not dry_run:
        from .indexer import build_index
        stats["stored"] = build_index(chunks, embedder, chroma_dir=config.CHROMA_DIR,
                                      collection_name=config.CHROMA_COLLECTION, reset=True)
    return stats
