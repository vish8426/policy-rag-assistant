"""Prompt construction for grounded, cited answers."""
from __future__ import annotations

import config

SYSTEM_PROMPT = (
    "You are the Helix Technologies policy assistant. Answer employee questions "
    "ONLY using the policy excerpts provided in the context. Follow these rules:\n"
    "1. Use only information found in the context. Do not use outside knowledge or "
    "guess.\n"
    "2. If the context does not contain the answer, reply exactly: "
    f"\"{config.REFUSAL_MESSAGE}\"\n"
    "3. Cite the source of each fact using its document ID in square brackets, "
    "e.g. [HR-002]. Cite every document you used.\n"
    "4. Be concise and factual. Keep the answer under 150 words.\n"
)


def format_context(chunks):
    blocks = []
    for c in chunks:
        header = f"[{c.doc_id}] {c.title} - Section: {c.section}"
        blocks.append(f"{header}\n{c.text}")
    return "\n\n---\n\n".join(blocks)


def build_messages(question, chunks):
    context = format_context(chunks)
    user = (
        f"Context (policy excerpts):\n\n{context}\n\n"
        f"Question: {question}\n\n"
        "Answer using only the context above, and cite document IDs in brackets."
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user},
    ]
