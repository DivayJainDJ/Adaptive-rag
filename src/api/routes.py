"""
API routes for RAG operations.
"""

from fastapi import APIRouter, UploadFile, File, Header
from langchain_core.messages import HumanMessage, AIMessage

from src.memory.chat_history_mongo import ChatHistory
from src.memory.chathistory_in_memory import ChatInMemoryHistory
from src.models.query_request import QueryRequest
from src.rag.document_upload import documents
from src.rag.graph_builder import builder
from src.db.mongo_client import client

router = APIRouter()
_use_mongo = None


async def _history(session_id: str):
    global _use_mongo
    if _use_mongo is None:
        try:
            await client.admin.command("ping")
            _use_mongo = True
            print("Using MongoDB chat history")
        except Exception as exc:
            _use_mongo = False
            print(f"MongoDB unavailable ({exc}); using in-memory chat history")

    if _use_mongo:
        return ChatHistory.get_session_history(session_id)

    memory = ChatInMemoryHistory.get_session_history(session_id)

    class _Adapter:
        async def add_message(self, message):
            memory.add_message(message)

        async def get_messages(self):
            return memory.messages

    return _Adapter()


@router.post("/rag/query")
async def rag_query(req: QueryRequest):
    try:
        chat_history = await _history(req.session_id)
        await chat_history.add_message(HumanMessage(content=req.query))
        messages = await chat_history.get_messages()
        result = builder.invoke({"messages": messages})
        output_text = result["messages"][-1].content
        await chat_history.add_message(AIMessage(content=output_text))
        return {
            "result": {"content": output_text},
            "route": result.get("route"),
        }
    except Exception as exc:
        from fastapi import HTTPException

        print(f"rag_query failed: {exc}")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rag/documents/upload")
async def upload_file(
    file: UploadFile = File(...),
    description: str = Header(..., alias="X-Description"),
):
    import asyncio
    # `documents()` does blocking I/O (file read + LLM call).
    # Run it in a thread executor so the event loop stays responsive.
    file_bytes = await file.read()

    # Reconstruct a sync-readable file-like object for the existing documents()
    import io
    file.file = io.BytesIO(file_bytes)

    loop = asyncio.get_event_loop()
    status_upload = await loop.run_in_executor(None, documents, description, file)
    return {"status": status_upload}
