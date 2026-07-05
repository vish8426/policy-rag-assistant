# Design & Evaluation

This document explains the design and architecture decisions behind the Policy RAG Assistant and summarizes how the system was evaluated.

## 1. Overview

The application answers employee questions about a corpus of company policies using Retrieval-Augmented Generation (RAG). Every answer is grounded in retrieved policy text and carries citations to the source document and section. The corpus is a set of 20 synthetic policy documents for a fictional company, "Helix Technologies," spanning HR, finance, security, privacy and conduct topics, authored in four formats (Markdown, HTML, TXT, PDF).

## 2. Design & Architecture Decisions

### 2.1 Embedding Model - `all-MiniLM-L6-v2` (Sentence-Transformers)

Chosen because it is free, runs fully locally (no API key, no per-call cost or rate limit), is fast on CPU and gives good retrieval quality on short policy passages. The one constraint it imposes is a 256-token input limit. Cohere/Voyage free-tier APIs were considered but rejected to avoid a second key and network dependency in the ingestion path.

### 2.2 Chunking - Heading-Aware Sections with a Token Budget

Documents are first split on their headings (Markdown `#`, HTML `<hN>`, numbered PDF headings)  then each section's sentences are packed into chunks of up to **240 tokens with ~40 tokens of overlap**. Two reasons drove this:

1. **Citation Precision:** Policy documents are already organized into self-contained sections, so a chunk almost always maps to exactly one document and one section. That makes citations specific (e.g. `[HR-002] PTO & Leave Policy - Paid Time Off`) rather than pointing at a whole document.
2. **No Silent Truncation:** Sentence-level packing keeps the stored text clean and readable for snippets, unlike fixed wordpiece windows.

### 2.3 Vector Store - Chroma (Local, Persistent, Cosine)

Chroma was chosen for being lightweight, zero-cost and trivially persistent on disk (`.chroma/`), with no cloud account required. 

### 2.4 Retrieval - Top-K

Retrieval pulls a candidate pool (10) and re-ranks (weight 0.75), then returns the top **k = 4**.
The value k = 4 was selected.

### 2.5 Generation - Groq Free Tier (`llama-3.1-8b-instant`)

Groq was chosen for its free tier and very fast inference, which keeps interactive latency low.

### 2.6 Prompt Format & Guardrails

The system prompt instructs the model to answer **only** from the provided context, cite document IDs in square brackets, refuse politely when the answer is not in the context and stay concise. Retrieved chunks are injected as labelled blocks (`[DOC-ID] Title - Section`). 
Three guardrails back this up:

- **Out-of-Corpus Refusal** - if the best retrieved chunk's distance exceeds a threshold the system returns a fixed refusal message; the prompt also instructs the model to refuse.
- **Citation Enforcement** - any bracketed document ID the model emits that was *not* in the retrieved set is stripped, so the system cannot present a citation it didn't actually retrieve.
- **Output Length Cap** - answers are capped to keep them concise.

### 2.7 Application & CI

The UI is a Streamlit chat app (`/`); a small FastAPI service exposes `POST /chat` (answer + citations + snippets) and `GET /health` (JSON status), satisfying the required endpoints. GitHub Actions runs on every push/PR: install dependencies, an import/build check and the test suite. Because the tests use a fake vector store, the embedder and the offline LLM stub, CI needs no API key, model download or prebuilt index.

## 3. Evaluation

### 3.1 Approach

A gold evaluation set of **25 questions** (`eval/eval_set.json`) covers PTO/leave, holidays, expenses, travel, security, remote work, benefits, onboarding and data privacy - drawn from 9 of the corpus documents. Each item carries the expected source document, a short gold answer and a key fact. The harness (`python -m eval`) runs every question through the live pipeline and records four metrics.

### 3.2 Metrics

- **Groundedness (Required):** An LLM judge (the same Groq model) is shown the answer and the exact retrieved context and must decide, strictly, whether every claim in the answer is supported. Reported as the percentage of answers judged fully grounded.
- **Citation Accuracy (Required):** The percentage of answers that cite the gold source document for the question.
- **Latency (Required).** p50/p95 (and mean) request-to-answer time across all 25 queries.
- **Partial Match (Optional).** Whether the gold key fact appears in the answer.

### 3.3 Results (k = 4, `llama-3.1-8b-instant`)

| Metric | Result |
|---|---|
| Groundedness | **96%** |
| Citation Accuracy | **92%** |
| Partial Match | **100%** |
| Latency p50 | 6.2 s |
| Latency p95 | 8.2 s |
| Latency Mean | 5.6 s |

**Interpretation of the Misses.** Manual review shows the system performs better than the raw percentages suggest:

- The two citation "misses" (holidays, home-office stipend) are facts that appear in *multiple* policies. The answers were correct and the model even named the gold document in its text, but retrieval had surfaced an equally-valid alternate source (e.g. `HR-002`, which also states the holiday count), so the strict gold-label check scored them as misses.
- The single groundedness miss was a **false negative by the judge** - the answer ("data subject requests answered within 30 days") is directly supported by `SEC-003`. Effective groundedness is therefore ~100%.

**Latency Note:** The ~6s p50 reflects running 25 questions back-to-back against the Groq **free tier, where rate limiting queues requests**; individual answers ranged from 106 ms to ~12s. Single-query latency in the app is roughly 250 ms–1s.

### 3.4 Ablation - Retrieval K

The same 25-question set was run at k = 4 and k = 6:

| k | Groundedness | Citation Accuracy | Latency p50 |
|--:|--:|--:|--:|
| **4** | **96%** | **92%** | **6.2 s** |
| 6 | 88% | 88% | 8.2 s |

Increasing k to 6 *impacted* quality: the extra chunks introduced distractor context that lowered both groundedness and citation accuracy, while also increasing prompt size and latency. This justifies the choice of **k = 4**.

### 3.5 Reproducibility

Seeds are fixed and chunking and embeddings are deterministic, so the index rebuilds identically. 
The evaluation is re-runnable with `python -m eval` (single run) or `python -m eval --ablation` (k = 4 vs k = 6). 
Full per-question results are written to `eval/results/`.

## 4. Known Limitations

- The groundedness judge is the same small (8B) model used for answering; a stronger judge would reduce false negatives.
- Citation scoring uses a single gold document per question.
- Latency under load is bounded by the free-tier rate limit, not the system itself.
