"""Streamlit chat UI for the Helix policy RAG assistant.

Run with:  streamlit run app/streamlit_app.py
This is the "/" web chat interface required by the project brief.
"""
from __future__ import annotations

import streamlit as st

import config
from rag.llm import resolve_provider
from rag.pipeline import RagPipeline

st.set_page_config(page_title="Helix Policy Assistant", page_icon="📘", layout="centered")


@st.cache_resource(show_spinner="Loading the policy index and model...")
def load_pipeline():
    return RagPipeline.from_config(provider="auto")


provider = resolve_provider("auto")
pipeline = load_pipeline()

# ---- Sidebar ----
with st.sidebar:
    st.header("Helix Policy Assistant")
    st.caption("Answers come only from the Helix policy corpus, with citations.")
    st.markdown(f"**LLM provider:** `{provider}`")
    st.markdown(f"**Model:** `{getattr(pipeline.llm, 'model', 'n/a')}`")
    st.markdown(f"**Top-k:** {pipeline.k}  |  **Re-rank:** {config.RERANK}")
    if provider == "stub":
        st.warning("No API key found — using the offline extractive stub. "
                   "Set GROQ_API_KEY in .env for full LLM answers.")
    st.divider()
    st.markdown("**Try asking:**")
    st.markdown("- How many PTO days do I get?\n- What is the meal per diem?\n"
                "- Is MFA required?\n- What's the home office stipend?")
    if st.button("Clear conversation"):
        st.session_state.messages = []
        st.rerun()

st.title("📘 Helix Policy Assistant")

if "messages" not in st.session_state:
    st.session_state.messages = []


def render_citations(citations):
    if not citations:
        return
    st.markdown("**Sources**")
    for c in citations:
        with st.expander(f"[{c['doc_id']}] {c['title']} — {c['section']}  ·  {c['source']}"):
            st.write(c["snippet"])


# Replay history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_citations(msg.get("citations", []))
            if msg.get("meta"):
                st.caption(msg["meta"])

# Input
if prompt := st.chat_input("Ask about company policies..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching the policies..."):
            result = pipeline.answer(prompt)
        st.markdown(result.answer)
        citations = [c.__dict__ for c in result.citations]
        render_citations(citations)
        meta = f"{result.model} · {result.latency_ms} ms" + (" · refused" if result.refused else "")
        st.caption(meta)

    st.session_state.messages.append({
        "role": "assistant",
        "content": result.answer,
        "citations": citations,
        "meta": meta,
    })
