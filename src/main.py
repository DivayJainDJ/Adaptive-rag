"""
Main FastAPI application entry point.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import router

app = FastAPI(title="Adaptive RAG API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.state.description_ = ""


@app.get("/")
async def root():
    return {"message": "Adaptive RAG API is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}
