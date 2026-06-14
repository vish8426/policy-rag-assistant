"""Guardrails: out-of-corpus refusal, citation enforcement, output length cap."""
from __future__ import annotations

import re

import config

_CITE_RE = re.compile(r"\[([A-Z]+-\d+)\]")


def is_out_of_corpus(chunks):
    """True if nothing retrieved is close enough to be on-topic."""
    if not chunks:
        return True
    best = min(c.distance for c in chunks)
    return best > config.RELEVANCE_MAX_DISTANCE


def enforce_citations(answer, allowed_doc_ids):
    """Drop any bracketed citation that is not one of the retrieved doc IDs."""
    allowed = set(allowed_doc_ids)
    cited = set(_CITE_RE.findall(answer))
    for bad in (cited - allowed):
        answer = answer.replace(f"[{bad}]", "")
    answer = re.sub(r"\s{2,}", " ", answer).strip()
    kept = [d for d in _CITE_RE.findall(answer) if d in allowed]
    # de-dup preserving order
    seen, ordered = set(), []
    for d in kept:
        if d not in seen:
            seen.add(d)
            ordered.append(d)
    return answer, ordered


def cap_words(text, max_words=160):
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]).rstrip(",.;:") + " ..."
