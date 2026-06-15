# Policy RAG Assistant

A Retrieval-Augmented Generation (RAG) application that answers questions about a corpus of company policies & procedures, with inline citations to the source documents. Built for the Quantic AI Engineering Project.

The corpus is a set of 20 synthetic policy documents for a fictional company, "Helix Technologies" (Markdown, HTML, TXT and PDF). Answers are grounded only in retrieved policy text; the assistant refuses questions outside the corpus.

- **Embeddings:** `all-MiniLM-L6-v2` (free, local)
- **Vector store:** Chroma (local, persistent, cosine)
- **LLM:** Groq free tier (`llama-3.1-8b-instant`); OpenRouter fallback; offline stub for tests
- **Retrieval:** top-k = 4 with a lexical re-rank
- **UI/API:** Streamlit chat + FastAPI `/chat` and `/health`

See [`design-and-evaluation.md`](design-and-evaluation.md) for design rationale and evaluation
results and [`ai-tooling.md`](ai-tooling.md) for how AI tools were used.

## Setup

Requires **Python 3.11** (3.13 lacks prebuilt wheels for some pinned dependencies).

```bash
# 1. Create and activate a virtual environment
py -3.11 -m venv .venv            # Windows
# python3.11 -m venv .venv        # macOS/Linux
.\.venv\Scripts\Activate.ps1      # Windows PowerShell
# source .venv/bin/activate       # macOS/Linux

# 2. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env              # then add your GROQ_API_KEY
```

A free Groq API key (https://console.groq.com) enables full LLM answers. Without a key the
app still runs using an offline extractive stub and the test suite always runs without one.

## Run

```bash
# 1. Build the vector index from the corpus (downloads the embedding model on first run)
python -m ingest

# 2a. Launch the chat UI  ->  http://localhost:8501
streamlit run app/streamlit_app.py

# 2b. (optional) Run the API  ->  http://127.0.0.1:8000  (docs at /docs)
uvicorn app.api:app --reload
```

API endpoints:

- `GET /health` - JSON status
- `POST /chat` - body `{"question": "..."}` returns the answer with citations and snippets
- `GET /` - service info

## Test

```bash
pytest -q
```

The suite (smoke, ingestion, RAG and API tests) is self-contained - no API key, model
download or prebuilt index required - and runs in CI on every push/PR
(`.github/workflows/ci.yml`).

## Evaluate

```bash
python -m eval              # 25-question eval: groundedness, citation accuracy, latency
python -m eval --ablation   # compare retrieval k = 4 vs k = 6
```

Results are written to `eval/results/`. Headline results (k = 4): **96% groundedness,
92% citation accuracy, 100% partial match, latency p50 6.2 s**. Details and analysis are in
[`design-and-evaluation.md`](design-and-evaluation.md).

## Project layout

| Path                  | Purpose                                             |
|-----------------------|-----------------------------------------------------|
| `corpus/`             | Synthetic company policy documents (md/html/txt/pdf)|
| `ingest/`             | Parse, chunk, embed, index into Chroma              |
| `rag/`                | Retrieval + prompt + LLM generation with guardrails |
| `app/`                | Streamlit UI + FastAPI endpoints                    |
| `eval/`               | Gold question set + evaluation harness + results    |
| `tests/`              | Smoke + unit + API tests                            |
| `config.py`           | Central settings and fixed seeds                    |
| `.github/workflows/`  | CI (install, import check, pytest)                  |

## Configuration

Key settings (overridable via `.env`, see `.env.example` and `config.py`): `LLM_PROVIDER`,
`GROQ_API_KEY`, `GROQ_MODEL`, `EMBEDDING_MODEL`, `TOP_K`, `CHUNK_SIZE_TOKENS`,
`CHROMA_DIR`, `SEED`.
