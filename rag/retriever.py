"""Top-k retrieval over the Chroma index, with an optional lexical re-rank.

The re-rank blends vector cosine similarity with simple query-term overlap, which
helps surface the chunk that actually mentions the asked-about terms (e.g. "per diem")
when several chunks are semantically close.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

import config

_WORD_RE = re.compile(r"\w+")


def _terms(text):
    return set(_WORD_RE.findall(text.lower()))


@dataclass
class RetrievedChunk:
    text: str
    doc_id: str
    title: str
    source: str
    section: str
    distance: float
    similarity: float
    score: float

    @property
    def citation_label(self):
        return f"[{self.doc_id}] {self.title} - {self.section}"


class Retriever:
    def __init__(self, collection, embedder, rerank=None):
        self.collection = collection
        self.embedder = embedder
        self.rerank = config.RERANK if rerank is None else rerank

    @classmethod
    def from_config(cls):
        from ingest.indexer import get_collection
        from ingest.embedder import get_embedder
        embedder = get_embedder("st", config.EMBEDDING_MODEL, config.EMBEDDING_DIM)
        collection = get_collection(config.CHROMA_DIR, config.CHROMA_COLLECTION)
        return cls(collection, embedder)

    def retrieve(self, query, k=None, candidates=None):
        k = k or config.TOP_K
        candidates = candidates or max(config.RETRIEVE_CANDIDATES, k)
        q_emb = self.embedder.embed([query])
        res = self.collection.query(
            query_embeddings=q_emb,
            n_results=candidates,
            include=["documents", "metadatas", "distances"],
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0]

        q_terms = _terms(query)
        chunks = []
        for text, meta, dist in zip(docs, metas, dists):
            sim = 1.0 - float(dist)
            if self.rerank and q_terms:
                overlap = len(q_terms & _terms(text)) / len(q_terms)
                score = 0.75 * sim + 0.25 * overlap
            else:
                score = sim
            chunks.append(RetrievedChunk(
                text=text,
                doc_id=meta.get("doc_id", "?"),
                title=meta.get("title", ""),
                source=meta.get("source", ""),
                section=meta.get("section", ""),
                distance=float(dist),
                similarity=sim,
                score=score,
            ))
        chunks.sort(key=lambda c: c.score, reverse=True)
        return chunks[:k]
