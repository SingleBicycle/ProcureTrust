from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import FastAPI
from pydantic import BaseModel


API_DIR = Path(__file__).resolve().parent
if str(API_DIR) not in sys.path:
    sys.path.append(str(API_DIR))

from services.audit import log_event  # noqa: E402
from services.state_machine import SessionState, apply_patch  # noqa: E402


app = FastAPI(title="ProcureTrust API", version="0.1.0")


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
    state = SessionState(session_id=session_id)
    log_event(
        session_id=session_id,
        event_type="state_transition",
        payload_json={"action": "create_session"},
        state_before=None,
        state_after=state,
    )
    return SessionResponse(id=session_id)


@app.post("/v1/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    session_id = request.session_id or str(uuid4())
    state_before = SessionState(session_id=session_id)

    log_event(
        session_id=session_id,
        event_type="user_msg",
        payload_json={"message": request.message},
        state_before=None,
        state_after=None,
    )

    category_input = {
        "text": request.message,
        "current_category_id": None,
    }
    category_output = {
        "category_id": "unknown",
        "confidence": 0.0,
        "alternatives": [],
    }
    log_event(
        session_id=session_id,
        event_type="tool_call",
        payload_json={
            "tool": "CategoryResolver",
            "input": category_input,
            "output": category_output,
        },
    )

    attribute_input = {
        "text": request.message,
        "current_category_id": None,
        "requirement_object": state_before.requirement_object,
    }
    attribute_output = {
        "patch": [],
        "confidence": 0.0,
    }
    log_event(
        session_id=session_id,
        event_type="tool_call",
        payload_json={
            "tool": "AttributeExtractor",
            "input": attribute_input,
            "output": attribute_output,
        },
    )

    patch = {}
    state_after = apply_patch(state_before, patch)
    log_event(
        session_id=session_id,
        event_type="state_transition",
        payload_json={"action": "apply_patch", "patch": patch},
        state_before=state_before,
        state_after=state_after,
    )

    return ChatResponse(reply="Placeholder response (audit wired).")
