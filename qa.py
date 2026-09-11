"""Builds the system prompt and calls the Anthropic API for SOP Q&A.

The full document text is sent as part of the system prompt on every call,
along with the running chat history, so follow-up questions have context.
There is no chunking or retrieval - the whole document goes in every time.
"""

from __future__ import annotations

import os

import anthropic
import streamlit as st

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 2048


def get_secret(key: str) -> str | None:
    """Read a value from st.secrets, falling back to None if no
    secrets.toml is configured (e.g. local dev without Streamlit secrets)."""
    try:
        return st.secrets.get(key)
    except Exception:
        return None

SYSTEM_PROMPT_TEMPLATE = """You are an assistant that answers questions about a single Standard Operating Procedure (SOP) document. You must follow these rules strictly:

1. Answer solely from the document text provided below. Never use general knowledge, and never guess. If the document does not contain the answer, say exactly: "The document doesn't cover this." Do not speculate about what the answer might be.
2. If a question is only partially covered by the document, answer the part that is covered, then explicitly state what the document does not address.
3. Every answer must cite the section heading or step number it came from (e.g. "Per Step 2: Collect Payment..." or "Per Section 3, Definitions...").
4. If the relevant step or section references an image (marked with the literal text "[image omitted]"), say that the document relies on a screenshot for that step, since you cannot see the image itself.
5. Do not fabricate section headings, step numbers, or content that is not actually present in the document below.

=== DOCUMENT START ===
{document_text}
=== DOCUMENT END ===
"""


def build_system_prompt(document_text: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(document_text=document_text)


def ask(document_text: str, chat_history: list[dict[str, str]]) -> str:
    """Send the document + chat history to the model and return the reply.

    `chat_history` is a list of {"role": "user"|"assistant", "content": str}
    dicts, ending with the latest user question.
    """
    api_key = get_secret("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set (checked st.secrets and the "
            "environment variable)."
        )

    client = anthropic.Anthropic(api_key=api_key)

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=build_system_prompt(document_text),
        messages=chat_history,
    )

    return "".join(
        block.text for block in response.content if block.type == "text"
    )
