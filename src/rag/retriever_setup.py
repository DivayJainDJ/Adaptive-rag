"""
Retriever setup and vector store configuration.
"""

from pathlib import Path

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

INDEX_DIR = Path(__file__).resolve().parents[2] / "faiss_index"
_embeddings = None
_faiss_vectorstore = None


def get_embeddings():
    """Load HuggingFace embeddings once (no OpenAI key required)."""
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
    return _embeddings


def retriever_chain(chunks: list[Document]):
    """
    Initialize and store documents in FAISS vector database.
    """
    global _faiss_vectorstore

    try:
        _faiss_vectorstore = FAISS.from_documents(
            documents=chunks,
            embedding=get_embeddings(),
        )
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        _faiss_vectorstore.save_local(str(INDEX_DIR))
        print("FAISS vector store initialized with documents")
        print(f"Vectorstore contains {len(chunks)} document chunks")
        return True
    except Exception as e:
        print(f"Error storing documents in FAISS: {e}")
        return False


def get_vectorstore():
    global _faiss_vectorstore
    if _faiss_vectorstore is not None:
        return _faiss_vectorstore
    if INDEX_DIR.exists():
        try:
            _faiss_vectorstore = FAISS.load_local(
                str(INDEX_DIR),
                get_embeddings(),
                allow_dangerous_deserialization=True,
            )
            return _faiss_vectorstore
        except Exception as exc:
            print(f"Could not load saved FAISS index: {exc}")
    return None


def get_base_retriever():
    """Return the current FAISS retriever, or None if nothing is indexed."""
    store = get_vectorstore()
    if store is None:
        return None
    return store.as_retriever(search_kwargs={"k": 4})


def search_uploaded_documents(query: str) -> str:
    """Search indexed documents; used by the ReAct agent as a tool."""
    retriever = get_base_retriever()
    if retriever is None:
        return "No documents have been uploaded yet. Please upload a document first."
    docs = retriever.invoke(query)
    if not docs:
        return "No relevant documents found."
    return "\n\n".join(doc.page_content for doc in docs)


def get_retriever():
    """
    Compatibility wrapper. Prefer get_base_retriever() or search_uploaded_documents().
    """
    return search_uploaded_documents
