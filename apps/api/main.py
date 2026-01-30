from __future__ import annotations

from typing import Optional
from uuid import uuid4

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="ProcureTrust API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class SessionResponse(BaseModel):
    id: str


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    reply: str


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/v1/sessions", response_model=SessionResponse)
def create_session() -> SessionResponse:
    session_id = str(uuid4())
    return SessionResponse(id=session_id)


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    _ = request
    return ChatResponse(reply="Placeholder response (orchestrator not wired yet).")
