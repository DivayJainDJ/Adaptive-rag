"""
Retriever setup and vector store configuration.
"""

import os

from langchain_core.documents import Document
from langchain_core.tools import create_retriever_tool
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from src.core.config import settings

embeddings = OpenAIEmbeddings()


def retriever_chain(chunks: list[Document]):
    """
    Initialize and store documents in Qdrant vector database.

    Args:
        chunks: List of document chunks to store.

    Returns:
        Boolean indicating success of the operation.
    """
    try:
        vectorstore = QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=embeddings,
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            collection_name=settings.CODE_COLLECTION,
        )
        print("Qdrant vector store initialized")
        print(vectorstore)
        return True
    except Exception as e:
        print(e)
        return False


def get_retriever():
    """
    Get a retriever tool connected to the Qdrant vector store.

    Loads description from file and creates a retriever tool with
    appropriate instructions based on the uploaded document description.

    Returns:
        A LangChain retriever tool configured for the vector store.

    Raises:
        Exception: If vector store initialization fails.
    """
    try:
        vectorstore = QdrantVectorStore.from_documents(
            documents=[],
            embedding=embeddings,
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            collection_name=settings.CODE_COLLECTION,
        )
        retriever = vectorstore.as_retriever()

        # Load document description
        if os.path.exists("description.txt"):
            with open("description.txt", "r", encoding="utf-8") as f:
                description = f.read()
        else:
            description = None

        retriever_tool = create_retriever_tool(
            retriever,
            "retriever_customer_uploaded_documents",
            f"Use this tool **only** to answer questions about: {description}\n"
            "Don't use this tool to answer anything else."
        )

        return retriever_tool


    except Exception as e:
        print(e)
        raise Exception(e)
