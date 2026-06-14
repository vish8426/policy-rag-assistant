"""FastAPI service exposing the policy RAG system.

Endpoints (as required by the project brief):
  GET  /health  -> simple JSON status
  POST /chat    -> {"question": ...} -> grounded answer with citations + snippets
  GET  /        -> basic service info
"""
from __future__ import annotations

import os
import sys
# Ensure the project root is importable (so `import config`, `rag`, `ingest`
# resolve even when launched via `streamlit run app/...`, which puts the
# script's own folder on sys.path instead of the project root).
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import os
from typing import List

from fastapi import Depends, FastAPI
from pydantic import BaseModel

import config

app = FastAPI(title="Helix Policy RAG", version="1.0")

# Lazily-built singleton so importing this module (e.g. in CI) is cheap and does
# not require the model/index until an actual /chat request is served.
_PIPELINE = None


def get_pipeline():
    global _PIPELINE
    if _PIPELINE is None:
        from rag.pipeline import RagPipeline
        _PIPELINE = RagPipeline.from_config(provider="auto")
    return _PIPELINE


class ChatRequest(BaseModel):
    question: str


class CitationOut(BaseModel):
    doc_id: str
    title: str
    source: str
    section: str
    snippet: str


class ChatResponse(BaseModel):
    question: str
    answer: str
    refused: bool
    model: str
    latency_ms: int
    citations: List[CitationOut]


@app.get("/")
def root():
    return {
        "service": "Helix Policy RAG",
        "endpoints": {"health": "GET /health", "chat": "POST /chat {question}"},
        "ui": "streamlit run app/streamlit_app.py",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "collection": config.CHROMA_COLLECTION,
        "index_present": os.path.isdir(config.CHROMA_DIR),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, pipeline=Depends(get_pipeline)):
    result = pipeline.answer(req.question)
    return ChatResponse(
        question=result.question,
        answer=result.answer,
        refused=result.refused,
        model=result.model,
        latency_ms=result.latency_ms,
        citations=[CitationOut(**c.__dict__) for c in result.citations],
    )
