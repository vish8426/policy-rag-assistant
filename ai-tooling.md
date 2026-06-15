# AI Tooling

This project was built with peer-programming help from AI tools, as per the assignment prompt. 
This document describes, in broad terms, which tools were used and how.

## Tools Used

- **AI Coding Assistant (Anthropic Claude, Agentic "Cowork" Mode):** Used as the primary development partner throughout. It helped with architecture decisions, generated most of the code and the synthetic policy corpus, wrote the tests and CI workflow, built the
  evaluation harness and helped debug environment issues. Work was done stage by stage (corpus -> ingestion -> RAG -> web app -> CI/CD -> evaluation -> docs), with review and testing at each step.
- **Groq (`llama-3.1-8b-instant`):** The runtime LLM that generates answers and acts as the judge during evaluation. Chosen for its free tier and fast inference.
- **Sentence-Transformers (`all-MiniLM-L6-v2`):** The free, local embedding model used for indexing and retrieval.

## How AI Assistance was Used

- **Design & Architecture:** Discussed and decided the stack (Chroma, Sentence-Transformers, Groq, Streamlit + FastAPI), the heading-aware chunking strategy and the guardrail design, with trade-offs weighed before committing. 
- **Code Generation:** The loaders, chunker, embedder, Chroma indexer, retriever, prompt and guardrail logic, the FastAPI service, the Streamlit UI, the test suite and the evaluation harness were AI-generated from specifications, then reviewed and run.
- **Corpus Authoring:** The 20 synthetic policy documents were generated with the assistant and kept internally consistent (shared figures such as PTO days and stipends) so that groundedness and citation scoring would be meaningful. A review and editing was performed per generated policy document.
- **Testing & CI:** The assistant designed self-contained tests (a fake vector store, a deterministic embedder and an offline LLM stub) so the suite and GitHub Actions run with no API key or model download and wrote the CI workflow.
- **Evaluation:** It built the metric definitions (LLM-judged groundedness, citation accuracy against a gold source, latency percentiles) and the k-ablation and helped interpret the results.

## What Worked Well

- **Rapid, End-to-End Scaffolding:** Going from an empty repo to a working, tested, CI-backed RAG app was fast, with clean module boundaries. 
- **Test Design.** Decoupling the tests from heavy dependencies (model, vector DB, API) made them fast, deterministic and CI-friendly.
- **Debugging Environment Problems:** The assistant quickly diagnosed a dependency build failure (a `numpy` source build on Python 3.13 with no compiler) and resolved it by moving the virtual environment to Python 3.11 and similarly fixed an import-path issue that only surfaced under `streamlit run`.
- **Evaluation Interpretation:** It correctly identified that the citation "misses" were multi-source facts and that one groundedness miss was a judge false negative, rather than treating the raw scores as the whole story.

## What Did Not Work as Well

- **Model/Version Assumptions:** Pinned library versions and the exact Groq model name needed checking against current docs rather than trusting defaults; the assistant verified the active model before relying on it.
- **A File-Watcher Corrupting Edits:** During development an editor/sync process intermittently truncated or inserted stray bytes into files mid-save; the fix was to write code via the shell and re-verify.
- **LLM-as-Judge NoiseL:** Using the same small 8B model as the groundedness judge produced an occasional false negative, which is a known limitation of cheap automated grading.
- **Free-Tier Rate Limits:** Running the evaluation back-to-back hit Groq's free-tier rate limit, inflating measured latency relative to interactive single-query use.
