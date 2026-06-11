# AI Engineering Project - Build Roadmap

A staged plan for building, evaluating and demoing a RAG application that answers questions about company policies. 

**Decisions Locked in:**
- **Scope:** Build the app + GitHub Actions CI/CD, demo locally (skip public deployment - it's optional in the rubric).
- **Stack:** Streamlit Chat UI + Chroma Vector DB, with a lightweight FastAPI module exposing `/chat` and `/health` (so satisfy the prompt's required endpoints and give CI a real smoke test).
- **Corpus:** Synthetic company policy documents author with AI assistance.
- **LLM / Embeddings:** Free-tier - Groq or OpenRouter for the LLM; a free embedding model (e.g. HuggingFace `all-MiniLM-L6-v2` locally or Cohere/Voyage free tier).

The rubric's top band (score 5) needs: a working RAG app with correct, citation-matched answers; clean architecture; CI/CD on push/PR; strong design docs; and evaluation covering **groundedness, citation accuracy and latency**.

---

## Stage 0 - Project Setup & Repo Skeleton

Goal: a clean, reproducible foundation before any feature work.

- Create the GitHub repo and local project structure.
- Set up a Python virtual environment (`venv`).
- Add `requirements.txt`, `.gitignore`, `.env.example` and a starter `README.md`.
- Decide folder layout (e.g. `corpus/`, `ingest/`, `rag/`, `app/`, `eval/`, `tests/`, `.github/workflows/`).
- Set fixed random seeds for deterministic chunking and eval sampling.

**Deliverable:** Empty-but-runnable repo skeleton, committed.

---

## Stage 1 - Author the Policy Corpus

Goal: 5–20 coherent synthetic policy docs, 30–120 pages total.

- Draft documents across the topics the evaluation expects: PTO/leave, security & acceptable use, expenses & reimbursement, remote work, holidays, code of conduct, benefits, onboarding, travel, data privacy.
- Write in a mix of formats (markdown primary; optionally a couple as PDF/HTML/TXT) so our parser handles multiple types as required.
- Keep them internally consistent (no contradicting policies) so groundedness scoring is fair.
- Store under `corpus/` with clear doc IDs/titles (used later for citations).

**Deliverable:** `corpus/` populated with the policy set.
*Maps to the "assemble a corpus" requirement.*

---

## Stage 2 - Ingestion & Indexing

Goal: turn the corpus into a searchable vector index.

- Build a loader that parses & cleans md / txt / HTML / PDF.
- Chunk documents (by headings and/or token windows with overlap), preserving doc ID + title + section for citations.
- Embed chunks with the chosen free embedding model.
- Store chunks + metadata + vectors in a local Chroma collection.
- Make ingestion a re-runnable script (`python -m ingest`) with seeds fixed.

**Deliverable:** `ingest/` pipeline + a built Chroma index.

---

## Stage 3 - RAG Pipeline (Retrieval + Generation)

Goal: the core question-answering engine.

- Implement Top-k retrieval over Chroma (optional re-ranking as a stretch).
- Build the prompt that injects retrieved chunks **with their source IDs/titles** into the LLM context.
- Wire up the free-tier LLM call (Groq/OpenRouter).
- Add guardrails: refuse out-of-corpus questions ("I can only answer about our policies"), cap output length, always cite source doc IDs/titles.
- Return a structured result: answer + citations + source snippets.

**Deliverable:** `rag/` module callable as a function; testable from a script before any UI.

---

## Stage 4 - Web Application

Goal: a usable chat interface plus the required API endpoints.

- `/health` - JSON status endpoint (FastAPI).
- `/chat` - POST endpoint: receives a question, returns answer + citations + snippets (FastAPI).
- `/` - Streamlit chat UI: text box for input, renders the answer with linked sources and snippets.
- Configuration via environment variables (API keys, model, DB path).

**Deliverable:** `app/` running locally - UI + API.

---

## Stage 5 - Tests & CI/CD

Goal: GitHub Actions runs on every push/PR.

- Add minimal tests: import check, `/health` smoke test and one retrieval/answer sanity test.
- Write `.github/workflows/ci.yml` that on push/PR installs deps, imports the app and runs `pytest -q`.
- Confirm the workflow goes green in GitHub.

**Deliverable:** Passing CI badge on the repo.
*Maps to prompt step 6 (CI/CD). Public deploy intentionally skipped - demo locally.*

---

## Stage 6 - Evaluation

Goal: quantify quality and speed - this is heavily weighted in the rubric.

- Write an evaluation set of 15–30 questions across policy topics, each with a short gold answer + expected source doc.
- **Groundedness** (required): % of answers fully supported by retrieved evidence.
- **Citation Accuracy** (required): % of answers whose citations point to the correct supporting passage.
- **Latency** (required): p50/p95 over 10–20 queries.
- Optional: exact/partial match vs gold answers; ablations over k / chunk size / prompt variants.
- Produce a results table/report fold into the design doc.

**Deliverable:** `eval/` harness + results.

---

## Stage 7 - Documentation

Goal: the written artifacts the submission requires.

- `README.md` - setup + run instructions (finalized).
- `design-and-evaluation.md` - architecture & design choices (embedding model, chunking, k, prompt format, vector store) + evaluation approach and results.
- `ai-tooling.md` - which AI tools used and how (what worked, what didn't).
- (Optional) `deployed.md` - skip unless  change our mind on deployment.

**Deliverable:** All docs committed.

---

## Stage 8 - Demo & submission

Goal: the final hand-in.

- Record a 5–10 minute screen-share demo: app in use, plus a walkthrough of design, evaluation and the CI run. (You speak + on camera + show government ID, per the rubric.)
- Share the repo with the `quantic-grader` GitHub account.
- Assemble the single submission PDF with two links: the repo and the demo video.

**Deliverable:** Submission PDF + shared repo + recorded demo.

---
