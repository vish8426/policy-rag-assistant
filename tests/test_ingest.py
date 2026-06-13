"""Stage 2 tests: corpus parsing + chunking (no embedding model / Chroma needed)."""
import config
from ingest.embedder import HashingEmbedder
from ingest.loaders import load_corpus
from ingest.chunker import chunk_documents

_tok = HashingEmbedder().count_tokens


def _load():
    return load_corpus(config.CORPUS_DIR)


def test_corpus_loads_all_formats():
    docs = _load()
    assert len(docs) >= 18
    fmts = {d.fmt for d in docs}
    assert {"md", "html", "txt", "pdf"} <= fmts          # every parser exercised
    for d in docs:
        assert d.doc_id and d.title and d.sections        # citation metadata present


def test_chunks_have_metadata_and_fit_budget():
    docs = _load()
    chunks = chunk_documents(docs, _tok, config.CHUNK_SIZE_TOKENS, config.CHUNK_OVERLAP_TOKENS)
    assert len(chunks) > len(docs)                        # docs split into multiple chunks
    required = {"doc_id", "title", "source", "format", "section", "chunk_index", "n_tokens"}
    for c in chunks:
        assert required <= set(c.metadata)
        assert c.text.strip()
        assert c.metadata["n_tokens"] <= config.CHUNK_SIZE_TOKENS
        assert c.id.startswith(c.metadata["doc_id"])


def test_known_doc_ids_present():
    ids = {d.doc_id for d in _load()}
    assert {"HR-002", "FIN-001", "SEC-001", "HR-008"} <= ids   # md + pdf(HR-008)
