"""Stage 3 tests: guardrails (unit) + RAG pipeline (integration, offline).

A lightweight in-memory stand-in for chromadb is installed so the pipeline can be
tested deterministically without a built index, the embedding model or API keys.
"""
import sys
import types
from types import SimpleNamespace

import pytest


# ---- install fake chromadb before importing chroma-dependent modules ----
class _FakeCollection:
    def __init__(self):
        self.ids = []; self.emb = []; self.docs = []; self.meta = []
    def add(self, ids, embeddings, documents, metadatas):
        self.ids += ids; self.emb += embeddings; self.docs += documents; self.meta += metadatas
    def count(self):
        return len(self.ids)
    def query(self, query_embeddings, n_results, include=None):
        q = query_embeddings[0]
        sim = lambda v: sum(a * b for a, b in zip(q, v))
        order = sorted(range(len(self.ids)), key=lambda i: sim(self.emb[i]), reverse=True)[:n_results]
        return {"ids": [[self.ids[i] for i in order]],
                "documents": [[self.docs[i] for i in order]],
                "metadatas": [[self.meta[i] for i in order]],
                "distances": [[1 - sim(self.emb[i]) for i in order]]}


class _FakeClient:
    store = {}
    def __init__(self, path=None): pass
    def delete_collection(self, n): _FakeClient.store.pop(n, None)
    def get_or_create_collection(self, name, metadata=None):
        return _FakeClient.store.setdefault(name, _FakeCollection())
    def get_collection(self, name):
        return _FakeClient.store[name]


_fake = types.ModuleType("chromadb")
_fake.PersistentClient = _FakeClient
sys.modules["chromadb"] = _fake

import config
from ingest.pipeline import run
from ingest.indexer import get_collection
from ingest.embedder import get_embedder
from rag.retriever import Retriever
from rag.llm import StubLLM
from rag.guardrails import enforce_citations, is_out_of_corpus
from rag.pipeline import RagPipeline


@pytest.fixture(scope="module")
def pipe():
    run(backend="hash", dry_run=False)
    emb = get_embedder("hash", config.EMBEDDING_MODEL, config.EMBEDDING_DIM)
    col = get_collection(config.CHROMA_DIR, config.CHROMA_COLLECTION)
    return RagPipeline(Retriever(col, emb), StubLLM())


def test_enforce_citations_drops_hallucinations():
    answer, kept = enforce_citations("PTO is 20 days [HR-002] per year [ZZ-999].", ["HR-002", "FIN-001"])
    assert kept == ["HR-002"]
    assert "ZZ-999" not in answer


def test_is_out_of_corpus_unit():
    assert is_out_of_corpus([]) is True
    far = [SimpleNamespace(distance=config.RELEVANCE_MAX_DISTANCE + 0.1)]
    near = [SimpleNamespace(distance=0.1)]
    assert is_out_of_corpus(far) is True
    assert is_out_of_corpus(near) is False


def test_answer_is_grounded_and_cited(pipe):
    r = pipe.answer("How many PTO days do full-time employees get each year?")
    assert r.refused is False
    assert "20 days" in r.answer
    assert any(c.doc_id == "HR-002" for c in r.citations)
    assert all(c.snippet for c in r.citations)
    assert r.latency_ms >= 0


def test_refuses_out_of_corpus(pipe):
    r = pipe.answer("What is the capital of France?")
    assert r.refused is True
    assert r.answer == config.REFUSAL_MESSAGE
