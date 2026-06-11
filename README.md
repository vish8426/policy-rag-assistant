# Policy RAG Assistant

A Retrieval-Augmented Generation (RAG) application that answers questions about a corpus
of company policies & procedures, with inline citations to the source documents.

Built for the Quantic AI Engineering Project.

> **Status:** In development. Stage 0 (environment & scaffolding) complete.
> See [`PROJECT-ROADMAP.md`](PROJECT-ROADMAP.md) for the full build plan.

## Architecture

- **Vector store:** Chroma (local, persisted)
- **Embeddings:** `all-MiniLM-L6-v2` (free, local)
- **LLM:** Groq free tier (OpenRouter as fallback)
- **UI/API:** Streamlit chat + FastAPI `/chat` and `/health`

## Setup

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env             # then add your GROQ_API_KEY
```

## Run

> Commands below are wired up in later stages.

```bash
# Build the vector index from the corpus (Stage 2)
python -m ingest

# Launch the chat UI (Stage 4)
streamlit run app/streamlit_app.py

# Run the API (Stage 4)
uvicorn app.api:app --reload
```

## Test

```bash
pytest -q
```

## Project Layout

| Path                  | Purpose                                            |
|-----------------------|----------------------------------------------------|
| `corpus/`             | Synthetic company policy documents                 |
| `ingest/`             | Parse, chunk, embed, index into Chroma             |
| `rag/`                | Retrieval + prompt + LLM generation with guardrails|
| `app/`                | Streamlit UI + FastAPI endpoints                   |
| `eval/`               | Evaluation set + groundedness/citation/latency     |
| `tests/`              | Smoke + unit tests                                  |
| `config.py`           | Central settings and fixed seeds                   |
| `.github/workflows/`  | CI/CD (install, import check, pytest)              |

## Documentation

- `design-and-evaluation.md` - design decisions + evaluation results (Stage 7)
- `ai-tooling.md` - AI tools used and how (Stage 7)
