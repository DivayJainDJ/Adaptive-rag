import os

from langchain_core.documents import Document
from langchain_core.tools import create_retriever_tool
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

from src.core.config import settings

embeddings = OpenAIEmbeddings()
def retriever_chain(chunks:list[Document]):
    # vectorStore = FAISS.from_documents(chunks, embeddings)
    # retriever = vectorStore.as_retriever()
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
    #retriever = vectorstore.as_retriever()

    #retriever_tool = create_retriever_tool(
    #    retriever,
    #    "retriever_vectorstore_langgraph",
    #    (
    #        "Use this tool **only** to answer questions about LangGraph documentation."
    #        "Don't use this tool to answer anything else"
    #    )
    #)
    #return retriever_tool

def get_retriever():
    try:
        vectorstore = QdrantVectorStore.from_documents(
            documents=[],
            embedding=embeddings,
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            collection_name=settings.CODE_COLLECTION,
        )
        retriever = vectorstore.as_retriever()
        if os.path.exists("description.txt"):
            with open("description.txt", "r", encoding="utf-8") as f:
                description = f.read()
        else:
            description = None
        retriever_tool = create_retriever_tool(
            retriever,
            "retriever_customer_uploaded_retriever",
            f"Use this tool **only** to answer questions about: {description}\n"
            "Don't use this tool to answer anything else."
        )
        return retriever_tool


    except Exception as e:
        print(e)
        raise Exception(e)
