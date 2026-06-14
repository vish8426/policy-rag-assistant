"""RAG orchestration: retrieve -> guardrail -> prompt -> generate -> cite."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List

import config
from .retriever import Retriever, RetrievedChunk
from .prompts import build_messages
from .guardrails import is_out_of_corpus, enforce_citations, cap_words
from .llm import get_llm


@dataclass
class Citation:
    doc_id: str
    title: str
    source: str
    section: str
    snippet: str


@dataclass
class RagResult:
    question: str
    answer: str
    citations: List[Citation] = field(default_factory=list)
    contexts: List[RetrievedChunk] = field(default_factory=list)
    refused: bool = False
    model: str = ""
    latency_ms: int = 0

    def to_dict(self):
        return {
            "question": self.question,
            "answer": self.answer,
            "refused": self.refused,
            "model": self.model,
            "latency_ms": self.latency_ms,
            "citations": [c.__dict__ for c in self.citations],
        }


class RagPipeline:
    def __init__(self, retriever, llm, k=None):
        self.retriever = retriever
        self.llm = llm
        self.k = k or config.TOP_K

    @classmethod
    def from_config(cls, provider=None):
        return cls(Retriever.from_config(), get_llm(provider))

    def _snippet(self, text):
        text = text.strip().replace("\n", " ")
        n = config.SNIPPET_CHARS
        return text if len(text) <= n else text[:n].rsplit(" ", 1)[0] + " ..."

    def _refusal(self, question, chunks, t0):
        return RagResult(
            question=question, answer=config.REFUSAL_MESSAGE, contexts=chunks,
            refused=True, model=getattr(self.llm, "model", ""),
            latency_ms=int((time.time() - t0) * 1000),
        )

    def answer(self, question):
        t0 = time.time()
        chunks = self.retriever.retrieve(question, k=self.k)

        if is_out_of_corpus(chunks):
            return self._refusal(question, chunks, t0)

        messages = build_messages(question, chunks)
        raw = cap_words(self.llm.complete(messages, max_tokens=config.MAX_OUTPUT_TOKENS))

        allowed = [c.doc_id for c in chunks]
        answer, cited_ids = enforce_citations(raw, allowed)

        if answer.strip().lower().startswith(config.REFUSAL_MESSAGE[:20].lower()):
            return self._refusal(question, chunks, t0)

        # Build citations from doc IDs the answer actually cited (fallback: best chunk).
        picked = cited_ids or ([chunks[0].doc_id] if chunks else [])
        citations, seen = [], set()
        for did in picked:
            if did in seen:
                continue
            seen.add(did)
            ch = next((c for c in chunks if c.doc_id == did), None)
            if ch:
                citations.append(Citation(ch.doc_id, ch.title, ch.source, ch.section,
                                          self._snippet(ch.text)))

        return RagResult(
            question=question, answer=answer, citations=citations, contexts=chunks,
            refused=False, model=getattr(self.llm, "model", ""),
            latency_ms=int((time.time() - t0) * 1000),
        )
