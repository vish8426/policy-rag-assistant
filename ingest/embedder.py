"""Embedding backends.

``SentenceTransformerEmbedder`` is the real, free, local embedder used by the app
(all-MiniLM-L6-v2). ``HashingEmbedder`` is a tiny, dependency-free deterministic
embedder used only for fast tests of the chunking + Chroma pipeline (no model
download, no torch). Both expose the same interface so they are interchangeable.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import List, Protocol


class Embedder(Protocol):
    dim: int

    def embed(self, texts: List[str]) -> List[List[float]]: ...

    def count_tokens(self, text: str) -> int: ...


class SentenceTransformerEmbedder:
    """Free local embeddings via sentence-transformers (all-MiniLM-L6-v2)."""

    def __init__(self, model_name: str, dim: int = 384):
        # Imported lazily so the rest of the pipeline (and tests) don't require torch.
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self._model = SentenceTransformer(model_name)
        self.dim = self._model.get_sentence_embedding_dimension() or dim
        self._tokenizer = self._model.tokenizer

    def embed(self, texts: List[str]) -> List[List[float]]:
        vecs = self._model.encode(
            texts,
            batch_size=32,
            normalize_embeddings=True,   # cosine-ready, deterministic
            show_progress_bar=False,
            convert_to_numpy=True,
        )
        return [v.tolist() for v in vecs]

    def count_tokens(self, text: str) -> int:
        return len(self._tokenizer.encode(text, add_special_tokens=False))


class HashingEmbedder:
    """Deterministic hashing embedder for tests. Not for production retrieval quality."""

    def __init__(self, dim: int = 384):
        self.dim = dim
        self._token_re = re.compile(r"\w+")

    def _tokens(self, text: str) -> List[str]:
        return self._token_re.findall(text.lower())

    def embed(self, texts: List[str]) -> List[List[float]]:
        out: List[List[float]] = []
        for text in texts:
            vec = [0.0] * self.dim
            for tok in self._tokens(text):
                h = int(hashlib.md5(tok.encode("utf-8")).hexdigest(), 16)
                vec[h % self.dim] += 1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            out.append([v / norm for v in vec])
        return out

    def count_tokens(self, text: str) -> int:
        # Approximate word-piece count; good enough for chunk budgeting in tests.
        return max(1, int(len(self._tokens(text)) * 1.3))


def get_embedder(backend: str, model_name: str, dim: int = 384) -> Embedder:
    backend = (backend or "st").lower()
    if backend in ("st", "sentence-transformers", "minilm"):
        return SentenceTransformerEmbedder(model_name, dim=dim)
    if backend in ("hash", "hashing", "test"):
        return HashingEmbedder(dim=dim)
    raise ValueError(f"Unknown embedder backend: {backend!r}")
