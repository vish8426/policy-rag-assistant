"""Stage 4 tests: FastAPI /health and /chat (offline, fake Chroma + stub LLM)."""
import sys
import types

import pytest
from fastapi.testclient import TestClient


# ---- fake chromadb (same approach as test_rag) ----
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
from rag.pipeline import RagPipeline
from app.api import app, get_pipeline


@pytest.fixture(scope="module")
def client():
    run(backend="hash", dry_run=False)
    emb = get_embedder("hash", config.EMBEDDING_MODEL, config.EMBEDDING_DIM)
    col = get_collection(config.CHROMA_DIR, config.CHROMA_COLLECTION)
    stub_pipe = RagPipeline(Retriever(col, emb), StubLLM())
    app.dependency_overrides[get_pipeline] = lambda: stub_pipe
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_chat_grounded(client):
    r = client.post("/chat", json={"question": "How many PTO days do full-time employees get?"})
    assert r.status_code == 200
    body = r.json()
    assert body["refused"] is False
    assert "20 days" in body["answer"]
    assert any(c["doc_id"] == "HR-002" for c in body["citations"])
    assert all(c["snippet"] for c in body["citations"])


def test_chat_refuses_out_of_corpus(client):
    r = client.post("/chat", json={"question": "What is the capital of France?"})
    assert r.json()["refused"] is True
