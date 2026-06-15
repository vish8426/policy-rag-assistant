"""Heading-aware chunking with a token budget.

Strategy:
  1. Start from the document's sections (already split on headings by the loader).
  2. Pack whole sentences into a chunk until adding the next sentence would exceed
     ``max_tokens``. This keeps chunks within the embedding model's input limit while
     preserving the original, citation-ready text (no sub-word artifacts).
  3. Carry the trailing ~``overlap_tokens`` of sentences into the next chunk so context
     isn't lost at chunk boundaries.

Most policy sections are short and become a single chunk, which makes citations precise
(a chunk maps to one document + one section).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, List

from .loaders import Document


@dataclass
class Chunk:
    id: str
    text: str
    metadata: Dict[str, object]


# Sentence splitter: break on ., !, ? followed by whitespace and on newlines/bullets.
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def _split_sentences(text: str) -> List[str]:
    parts = [p.strip() for p in _SENT_SPLIT_RE.split(text)]
    return [p for p in parts if p]


def _split_long_sentence(sentence: str, count_tokens: Callable[[str], int], max_tokens: int) -> List[str]:
    """Fallback for a single sentence longer than the budget: split on words."""
    words = sentence.split()
    out: List[str] = []
    cur: List[str] = []
    for w in words:
        cur.append(w)
        if count_tokens(" ".join(cur)) >= max_tokens:
            out.append(" ".join(cur))
            cur = []
    if cur:
        out.append(" ".join(cur))
    return out


def _pack_sentences(
    sentences: List[str],
    count_tokens: Callable[[str], int],
    max_tokens: int,
    overlap_tokens: int,
) -> List[str]:
    """Greedily pack sentences into <= max_tokens windows with sentence-level overlap."""
    chunks: List[str] = []
    cur: List[str] = []

    def cur_tokens() -> int:
        return count_tokens(" ".join(cur)) if cur else 0

    for sent in sentences:
        if count_tokens(sent) > max_tokens:
            # Flush current, then hard-split the oversized sentence.
            if cur:
                chunks.append(" ".join(cur))
                cur = []
            chunks.extend(_split_long_sentence(sent, count_tokens, max_tokens))
            continue

        if cur and count_tokens(" ".join(cur + [sent])) > max_tokens:
            chunks.append(" ".join(cur))
            # Build overlap: keep trailing sentences up to overlap_tokens.
            overlap: List[str] = []
            for s in reversed(cur):
                if count_tokens(" ".join([s] + overlap)) > overlap_tokens:
                    break
                overlap.insert(0, s)
            cur = overlap + [sent]
        else:
            cur.append(sent)

    if cur:
        chunks.append(" ".join(cur))
    return chunks


def chunk_document(
    doc: Document,
    count_tokens: Callable[[str], int],
    max_tokens: int,
    overlap_tokens: int,
) -> List[Chunk]:
    """Turn one Document into a list of Chunks with citation metadata."""
    chunks: List[Chunk] = []
    idx = 0
    for section in doc.sections:
        sentences = _split_sentences(section.text)
        if not sentences:
            continue
        for piece in _pack_sentences(sentences, count_tokens, max_tokens, overlap_tokens):
            chunk_id = f"{doc.doc_id}::{idx:03d}"
            chunks.append(
                Chunk(
                    id=chunk_id,
                    text=piece,
                    metadata={
                        "doc_id": doc.doc_id,
                        "title": doc.title,
                        "source": doc.source,
                        "format": doc.fmt,
                        "section": section.heading,
                        "chunk_index": idx,
                        "n_tokens": count_tokens(piece),
                    },
                )
            )
            idx += 1
    return chunks


def chunk_documents(
    docs: List[Document],
    count_tokens: Callable[[str], int],
    max_tokens: int,
    overlap_tokens: int,
) -> List[Chunk]:
    out: List[Chunk] = []
    for doc in docs:
        out.extend(chunk_document(doc, count_tokens, max_tokens, overlap_tokens))
    return out
