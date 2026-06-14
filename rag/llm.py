"""LLM clients: Groq and OpenRouter (free-tier), plus an offline deterministic stub."""
from __future__ import annotations

import re

import config

# Common words ignored when the offline stub scores relevance, so out-of-corpus
# questions (no meaningful content-word overlap) produce a refusal.
_STOP = {
    "the", "a", "an", "of", "to", "is", "are", "do", "does", "did", "i", "we", "you",
    "my", "our", "what", "which", "who", "how", "when", "where", "why", "can", "may",
    "for", "in", "on", "at", "and", "or", "be", "with", "as", "if", "it", "this",
    "that", "get", "have", "has", "many", "much", "about",
}


def _content_terms(text):
    return {w for w in re.findall(r"\w+", text.lower()) if w not in _STOP and len(w) > 1}


class StubLLM:
    """Offline, deterministic 'LLM' for tests and no-key demos.

    Extracts the context sentence with the most query content-word overlap and
    appends its document-ID citation, mimicking a grounded answer with no API call.
    Returns the refusal message when no content words overlap.
    """
    model = "stub-extractive"

    def complete(self, messages, **kwargs):
        user = messages[-1]["content"]
        context = user.split("Question:")[0]
        m = re.search(r"Question:\s*(.*?)\n", user + "\n")
        q_terms = _content_terms(m.group(1) if m else "")

        best_id, best_sentence, best_score = None, "", 0
        for block in context.split("\n\n---\n\n"):
            header, _, body = block.partition("\n")
            mid = re.match(r"\[([A-Z]+-\d+)\]", header.strip())
            doc_id = mid.group(1) if mid else None
            for sent in re.split(r"(?<=[.!?])\s+", body):
                score = len(q_terms & _content_terms(sent))
                if score > best_score and sent.strip():
                    best_id, best_sentence, best_score = doc_id, sent.strip(), score
        if best_score <= 0 or not best_sentence:
            return config.REFUSAL_MESSAGE
        return f"{best_sentence}{(' [' + best_id + ']') if best_id else ''}"


class _OpenAICompatLLM:
    def __init__(self, api_key, model, base_url=None):
        from openai import OpenAI
        self._client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        self.model = model

    def complete(self, messages, max_tokens=None, temperature=None):
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens or config.MAX_OUTPUT_TOKENS,
            temperature=config.LLM_TEMPERATURE if temperature is None else temperature,
            timeout=config.LLM_TIMEOUT_SECONDS,
        )
        return (resp.choices[0].message.content or "").strip()


class GroqLLM:
    def __init__(self, api_key=None, model=None):
        from groq import Groq
        self._client = Groq(api_key=api_key or config.GROQ_API_KEY)
        self.model = model or config.GROQ_MODEL

    def complete(self, messages, max_tokens=None, temperature=None):
        resp = self._client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=max_tokens or config.MAX_OUTPUT_TOKENS,
            temperature=config.LLM_TEMPERATURE if temperature is None else temperature,
        )
        return (resp.choices[0].message.content or "").strip()


def resolve_provider(provider=None):
    """Resolve 'auto' to a concrete provider based on available API keys."""
    provider = (provider or config.LLM_PROVIDER).lower()
    if provider == "auto":
        if config.GROQ_API_KEY:
            return "groq"
        if config.OPENROUTER_API_KEY:
            return "openrouter"
        return "stub"
    return provider


def get_llm(provider=None):
    provider = resolve_provider(provider)
    if provider == "stub":
        return StubLLM()
    if provider == "groq":
        return GroqLLM()
    if provider == "openrouter":
        return _OpenAICompatLLM(config.OPENROUTER_API_KEY, config.OPENROUTER_MODEL,
                                base_url="https://openrouter.ai/api/v1")
    raise ValueError(f"Unknown LLM provider: {provider!r}")
