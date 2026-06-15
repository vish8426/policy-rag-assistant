"""Evaluate the RAG system: groundedness, citation accuracy, latency (+ optional partial match).

- Groundedness: an LLM judge decides whether every claim in the answer is supported by the
  retrieved context (the same evidence the answer was generated from).
- Citation accuracy: does the answer cite the gold source document for the question.
- Latency: p50/p95 (and mean) over all queries, measured request-to-answer.
- Partial match (optional): is the gold key fact present in the answer.

Run a single evaluation:        python -m eval
Run a k-ablation (k=4 vs k=6):  python -m eval --ablation
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

EVAL_PATH = Path(__file__).resolve().parent / "eval_set.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

JUDGE_SYSTEM = (
    "You are a strict evaluator. Decide whether EVERY factual claim in the ANSWER is "
    "directly supported by the provided CONTEXT. If anything in the answer is not supported "
    "by the context, reply NO. Reply with a single word: YES or NO."
)


def percentile(values, pct):
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * pct / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return float(s[f])
    return float(s[f] + (s[c] - s[f]) * (k - f))


def judge_grounded(judge_llm, answer, contexts):
    ctx = "\n\n".join(f"[{c.doc_id}] {c.text}" for c in contexts)
    messages = [
        {"role": "system", "content": JUDGE_SYSTEM},
        {"role": "user", "content": f"CONTEXT:\n{ctx}\n\nANSWER:\n{answer}\n\n"
                                    "Is every claim in the ANSWER supported by the CONTEXT? Reply YES or NO."},
    ]
    out = judge_llm.complete(messages, max_tokens=5, temperature=0)
    return out.strip().upper().startswith("Y")


def _score(pipe, items, judge_llm=None, grounded_fn=None):
    """Run the pipeline over items and compute the metric summary + rows (no file writes)."""
    rows, latencies = [], []
    n_cit = n_ground = n_partial = 0
    for it in items:
        res = pipe.answer(it["question"])
        latencies.append(res.latency_ms)
        cited = [c.doc_id for c in res.citations]
        cit_ok = it["expected_doc_id"] in cited
        partial = it.get("key_fact", "").lower() in res.answer.lower()
        grounded = grounded_fn(res.answer, res.contexts) if grounded_fn else judge_grounded(judge_llm, res.answer, res.contexts)
        n_cit += int(cit_ok)
        n_ground += int(grounded)
        n_partial += int(partial)
        rows.append({
            "id": it["id"], "question": it["question"], "answer": res.answer,
            "expected_doc_id": it["expected_doc_id"], "cited": cited,
            "citation_correct": cit_ok, "grounded": grounded, "partial_match": partial,
            "refused": res.refused, "latency_ms": res.latency_ms, "model": res.model,
        })
    total = len(items)
    summary = {
        "total_questions": total,
        "top_k": pipe.k,
        "rerank": config.RERANK,
        "groundedness_pct": round(100 * n_ground / total, 1),
        "citation_accuracy_pct": round(100 * n_cit / total, 1),
        "partial_match_pct": round(100 * n_partial / total, 1),
        "latency_p50_ms": round(percentile(latencies, 50), 1),
        "latency_p95_ms": round(percentile(latencies, 95), 1),
        "latency_mean_ms": round(sum(latencies) / len(latencies), 1) if latencies else 0,
        "model": rows[0]["model"] if rows else "",
        "embedding_model": config.EMBEDDING_MODEL,
    }
    return summary, rows


def _load_items(eval_path):
    return json.loads(Path(eval_path).read_text(encoding="utf-8"))


def _build():
    from rag.pipeline import RagPipeline
    from rag.llm import get_llm
    return RagPipeline.from_config(provider="auto"), get_llm("auto")


def run_eval(pipe=None, judge_llm=None, eval_path=EVAL_PATH, grounded_fn=None):
    config.set_seeds()
    items = _load_items(eval_path)
    if pipe is None:
        pipe, judge_llm = _build()
    elif judge_llm is None and grounded_fn is None:
        from rag.llm import get_llm
        judge_llm = get_llm("auto")

    summary, rows = _score(pipe, items, judge_llm=judge_llm, grounded_fn=grounded_fn)
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "eval_results.json").write_text(
        json.dumps({"summary": summary, "rows": rows}, indent=2), encoding="utf-8")
    _write_markdown(summary, rows)
    return summary, rows


def run_ablation(k_values=(4, 6), eval_path=EVAL_PATH):
    """Run the eval at several retrieval k values, reusing one pipeline + judge."""
    config.set_seeds()
    items = _load_items(eval_path)
    pipe, judge_llm = _build()

    results = {}
    headline = None
    for k in k_values:
        pipe.k = k
        summary, rows = _score(pipe, items, judge_llm=judge_llm)
        results[k] = summary
        if k == config.TOP_K or headline is None:
            headline = (summary, rows)

    # Headline files reflect the default k (config.TOP_K) or the first k tried.
    RESULTS_DIR.mkdir(exist_ok=True)
    (RESULTS_DIR / "eval_results.json").write_text(
        json.dumps({"summary": headline[0], "rows": headline[1]}, indent=2), encoding="utf-8")
    _write_markdown(headline[0], headline[1])
    _write_ablation(results)
    return results


def _write_markdown(summary, rows):
    L = []
    L.append("# RAG Evaluation Results\n")
    L.append(f"- Model: `{summary['model']}`  |  Embeddings: `{summary['embedding_model']}`  "
             f"|  Top-k: {summary['top_k']}  |  Re-rank: {summary['rerank']}")
    L.append(f"- Questions: {summary['total_questions']}\n")
    L.append("## Summary\n")
    L.append("| Metric | Value |")
    L.append("|---|---|")
    L.append(f"| Groundedness | {summary['groundedness_pct']}% |")
    L.append(f"| Citation accuracy | {summary['citation_accuracy_pct']}% |")
    L.append(f"| Partial match (gold fact) | {summary['partial_match_pct']}% |")
    L.append(f"| Latency p50 | {summary['latency_p50_ms']} ms |")
    L.append(f"| Latency p95 | {summary['latency_p95_ms']} ms |")
    L.append(f"| Latency mean | {summary['latency_mean_ms']} ms |\n")
    L.append("## Per-question results\n")
    L.append("| # | Question | Expected | Cited | Cite | Grnd | Match | Latency |")
    L.append("|--:|---|---|---|:--:|:--:|:--:|--:|")
    for r in rows:
        L.append(f"| {r['id']} | {r['question']} | {r['expected_doc_id']} | "
                 f"{', '.join(r['cited']) or '-'} | {'Y' if r['citation_correct'] else 'N'} | "
                 f"{'Y' if r['grounded'] else 'N'} | {'Y' if r['partial_match'] else 'N'} | {r['latency_ms']} ms |")
    (RESULTS_DIR / "eval_summary.md").write_text("\n".join(L) + "\n", encoding="utf-8")


def _write_ablation(results):
    (RESULTS_DIR / "ablation.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    L = ["# Ablation: retrieval top-k\n",
         "Same 25-question set and model; only the number of retrieved chunks (k) changes.\n",
         "| k | Groundedness | Citation accuracy | Partial match | Latency p50 | Latency p95 |",
         "|--:|--:|--:|--:|--:|--:|"]
    for k, s in results.items():
        L.append(f"| {k} | {s['groundedness_pct']}% | {s['citation_accuracy_pct']}% | "
                 f"{s['partial_match_pct']}% | {s['latency_p50_ms']} ms | {s['latency_p95_ms']} ms |")
    (RESULTS_DIR / "ablation.md").write_text("\n".join(L) + "\n", encoding="utf-8")
