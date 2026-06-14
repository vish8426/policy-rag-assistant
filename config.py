"""Central configuration and reproducibility settings."""
from __future__ import annotations

import os
import random
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# --- Paths ---
ROOT_DIR = Path(__file__).resolve().parent
CORPUS_DIR = ROOT_DIR / "corpus"

# --- Reproducibility ---
SEED = int(os.getenv("SEED", "42"))


def set_seeds(seed=SEED):
    """Fix seeds for deterministic chunking and evaluation sampling."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except Exception:
        pass


# --- LLM ---
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.0"))
LLM_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "30"))

# --- Embeddings ---
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "384"))

# --- Vector store ---
CHROMA_DIR = os.getenv("CHROMA_DIR", str(ROOT_DIR / ".chroma"))
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "policies")

# --- Chunking (kept at/below the embedding model's 256-token input limit) ---
CHUNK_SIZE_TOKENS = int(os.getenv("CHUNK_SIZE_TOKENS", "240"))
CHUNK_OVERLAP_TOKENS = int(os.getenv("CHUNK_OVERLAP_TOKENS", "40"))

# --- Retrieval / generation ---
TOP_K = int(os.getenv("TOP_K", "4"))
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "512"))
# Blend vector similarity with lexical overlap when ranking (cheap re-rank).
RERANK = os.getenv("RERANK", "true").lower() in ("1", "true", "yes")
# Pull a larger candidate pool before re-ranking down to TOP_K.
RETRIEVE_CANDIDATES = int(os.getenv("RETRIEVE_CANDIDATES", "10"))
# Refuse to answer when the best chunk's cosine distance exceeds this (out-of-corpus gate).
RELEVANCE_MAX_DISTANCE = float(os.getenv("RELEVANCE_MAX_DISTANCE", "0.75"))
# Characters of each chunk shown as a citation snippet.
SNIPPET_CHARS = int(os.getenv("SNIPPET_CHARS", "240"))

# --- Guardrail copy ---
REFUSAL_MESSAGE = "I can only answer questions about our company policies."
