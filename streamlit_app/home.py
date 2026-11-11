"""
Home page for Streamlit Adaptive RAG application.
"""

import logging
import uuid

import streamlit as st

import sys, os
import requests
sys.path.insert(0, os.path.dirname(__file__))
from utils.api_client import PYTHON_BASE_URL, document_upload_rag, query_backend

st.set_page_config(page_title="Adaptive RAG", page_icon="🤖")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filename="app.log",
    filemode="a",
)

# Create a session ID locally.
if "session_id" not in st.session_state:
    st.session_state["session_id"] = str(uuid.uuid4())

if "username" not in st.session_state:
    st.session_state["username"] = "Guest"

st.title("🤖 Adaptive RAG Assistant")

try:
    health = requests.get(f"{PYTHON_BASE_URL}/health", timeout=2)
    if health.ok:
        st.success(f"Connected to Adaptive RAG backend at {PYTHON_BASE_URL}")
    else:
        st.error(f"Backend at {PYTHON_BASE_URL} returned HTTP {health.status_code}")
except requests.RequestException as exc:
    st.error(f"Backend is not reachable at {PYTHON_BASE_URL}. Start FastAPI on port 8001. ({exc})")

st.write(
    f"Session: `{st.session_state['session_id']}`"
)

st.divider()

# Document upload
st.subheader("📄 Upload a Document")

uploaded_file = st.file_uploader(
    "Upload a PDF or TXT document",
    type=["pdf", "txt"],
)

description = st.text_input(
    "Document description",
    placeholder="Describe this document...",
)

if st.button("Upload Document"):
    if uploaded_file is None:
        st.error("Please select a document first.")
    elif not description:
        st.error("Please provide a document description.")
    else:
        success = document_upload_rag(
            uploaded_file,
            description,
        )

        if success:
            st.success("Document uploaded successfully!")
        else:
            st.error("Document upload failed.")

st.divider()

# Chat
st.subheader("💬 Ask Adaptive RAG")

query = st.chat_input("Ask a question about your documents...")

if query:
    with st.chat_message("user"):
        st.write(query)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = query_backend(
                query,
                st.session_state["session_id"],
            )

        st.write(response)

# Debug logs
with st.expander("📜 Debug Logs"):
    try:
        with open("app.log", "r") as log_file:
            st.text(log_file.read())
    except FileNotFoundError:
        st.warning("Log file not found yet.")
