"""Streamlit UI for single-document SOP question answering."""

from __future__ import annotations

import datetime
import os

import streamlit as st

import extract
import qa

CHARS_PER_TOKEN = 4
TOKEN_WARNING_THRESHOLD = 150_000
LOG_PATH = os.path.join(os.path.dirname(__file__), "logs", "questions.log")

st.set_page_config(page_title="SOP Q&A", page_icon="📋")


def _render_login():
    st.title("SOP Q&A")
    st.subheader("Login required")

    def _check_password():
        entered = st.session_state.get("password_input", "")
        expected = qa.get_secret("APP_PASSWORD")
        if expected and entered == expected:
            st.session_state.authenticated = True
        else:
            st.session_state.auth_error = True

    st.text_input(
        "Password", type="password", key="password_input", on_change=_check_password
    )
    if st.session_state.get("auth_error"):
        st.error("Incorrect password.")


def _reset_chat():
    st.session_state.messages = []


def _log_question(filename: str, question: str, answer: str):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    answer_snippet = answer[:100].replace("\n", " ")
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(f"{timestamp}\t{filename}\t{question}\t{answer_snippet}\n")


def _load_document(uploaded_file):
    filename = uploaded_file.name
    try:
        result = extract.extract(uploaded_file, filename)
    except ValueError as e:
        st.session_state.document_text = None
        st.session_state.doc_error = str(e)
        return

    if isinstance(result, tuple):
        text, page_count = result
    else:
        text, page_count = result, None

    st.session_state.document_text = text
    st.session_state.doc_error = None
    st.session_state.filename = filename
    st.session_state.word_count = len(text.split())
    st.session_state.page_count = page_count
    _reset_chat()


def _render_sidebar():
    st.sidebar.header("Document")
    uploaded_file = st.sidebar.file_uploader(
        "Upload an SOP document", type=["docx", "pdf", "txt", "md"]
    )

    if uploaded_file is not None:
        current_id = (uploaded_file.name, uploaded_file.size)
        if st.session_state.get("loaded_file_id") != current_id:
            st.session_state.loaded_file_id = current_id
            _load_document(uploaded_file)

    if st.session_state.get("doc_error"):
        st.sidebar.error(st.session_state.doc_error)
        return

    if st.session_state.get("document_text"):
        st.sidebar.success(f"Loaded: {st.session_state.filename}")
        stats = f"{st.session_state.word_count:,} words"
        if st.session_state.page_count is not None:
            stats += f" · {st.session_state.page_count} pages"
        st.sidebar.caption(stats)

        est_tokens = len(st.session_state.document_text) // CHARS_PER_TOKEN
        if est_tokens > TOKEN_WARNING_THRESHOLD:
            st.sidebar.warning(
                f"This document is large (~{est_tokens:,} estimated tokens). "
                "Answers may be slower or less reliable."
            )


def _render_chat():
    if not st.session_state.get("document_text"):
        st.info("Upload an SOP document in the sidebar to get started.")
        return

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    question = st.chat_input("Ask a question about the document")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                answer = qa.ask(
                    st.session_state.document_text, st.session_state.messages
                )
            except RuntimeError as e:
                answer = f"Error: {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    _log_question(st.session_state.filename, question, answer)


def main():
    if not st.session_state.get("authenticated"):
        _render_login()
        return

    st.title("SOP Q&A")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    _render_sidebar()
    _render_chat()


if __name__ == "__main__":
    main()
