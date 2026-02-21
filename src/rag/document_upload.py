import os
import tempfile
from http.client import HTTPException

from fastapi import UploadFile, File
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.retriever_setup import retriever_chain
from src.tools.common_tools import enhance_description_with_llm


def documents(description: str, file: UploadFile = File(...)):
    filename = file.filename
    if not filename.endswith(".pdf") and not filename.endswith(".txt"):
        raise HTTPException(status_code=400, detail="Only PDF and TXT files are supported")

    file_bytes = file.file.read()


    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
        tmp_file.write(file_bytes)
        tmp_path = tmp_file.name

    if filename.endswith(".pdf"):
        loader = PyPDFLoader(tmp_path)
    else:
        loader = TextLoader(tmp_path, encoding="utf-8")

    try:
        docs = loader.load()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading file: {e}")
    finally:
        os.unlink(tmp_path)
    description_llm=enhance_description_with_llm(description)
    #print("collection_metadata")
    #print(collection_metadata)
    with open("description.txt", "w", encoding="utf-8") as f:
        f.write(description_llm)

    with open("description.txt", "r", encoding="utf-8") as f:
        print("document from storage")
        print(f.read())

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    chunks= splitter.split_documents(docs)
    return retriever_chain(chunks)




