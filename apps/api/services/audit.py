from __future__ import annotations

import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from pydantic import BaseModel, ConfigDict


EVENT_TYPES = {
    "user_msg",
    "assistant_msg",
    "tool_call",
    "state_transition",
    "error",
}


class AuditEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: Optional[int] = None
    session_id: str
    ts: float
    event_type: str
    payload_json: Dict[str, Any]
    state_before_json: Optional[Dict[str, Any]] = None
    state_after_json: Optional[Dict[str, Any]] = None


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def audit_db_path() -> Path:
    env_path = os.getenv("AUDIT_DB_PATH")
    if env_path:
        return Path(env_path)
    return _repo_root() / "apps" / "api" / "audit.db"


def _connect() -> sqlite3.Connection:
    path = audit_db_path()
    if str(path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS audit_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            ts REAL NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            state_before_json TEXT,
            state_after_json TEXT
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_audit_session_ts
        ON audit_events(session_id, ts, id)
        """
    )
    conn.commit()


def _dump_json(value: Optional[Dict[str, Any]]) -> Optional[str]:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=True, sort_keys=True)


def _load_json(value: Optional[str]) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    return json.loads(value)


def serialize_state(state: Any) -> Optional[Dict[str, Any]]:
    if state is None:
        return None
    if hasattr(state, "model_dump"):
        return state.model_dump()
    if isinstance(state, dict):
        return state
    return {"value": state}


def record_event(event: AuditEvent, conn: Optional[sqlite3.Connection] = None) -> int:
    if event.event_type not in EVENT_TYPES:
        raise ValueError(f"Unsupported event_type: {event.event_type}")
    owns_conn = conn is None
    if conn is None:
        conn = _connect()
    try:
        cursor = conn.execute(
            """
            INSERT INTO audit_events (
                session_id,
                ts,
                event_type,
                payload_json,
                state_before_json,
                state_after_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                event.session_id,
                event.ts,
                event.event_type,
                _dump_json(event.payload_json) or "{}",
                _dump_json(event.state_before_json),
                _dump_json(event.state_after_json),
            ),
        )
        conn.commit()
        return int(cursor.lastrowid)
    finally:
        if owns_conn:
            conn.close()


def log_event(
    session_id: str,
    event_type: str,
    payload_json: Dict[str, Any],
    state_before: Any = None,
    state_after: Any = None,
) -> int:
    event = AuditEvent(
        session_id=session_id,
        ts=time.time(),
        event_type=event_type,
        payload_json=payload_json,
        state_before_json=serialize_state(state_before),
        state_after_json=serialize_state(state_after),
    )
    return record_event(event)


def fetch_events(
    session_id: str,
    conn: Optional[sqlite3.Connection] = None,
) -> List[AuditEvent]:
    owns_conn = conn is None
    if conn is None:
        conn = _connect()
    try:
        rows = conn.execute(
            """
            SELECT id, session_id, ts, event_type, payload_json, state_before_json, state_after_json
            FROM audit_events
            WHERE session_id = ?
            ORDER BY ts ASC, id ASC
            """,
            (session_id,),
        ).fetchall()
        events = []
        for row in rows:
            events.append(
                AuditEvent(
                    id=row["id"],
                    session_id=row["session_id"],
                    ts=row["ts"],
                    event_type=row["event_type"],
                    payload_json=_load_json(row["payload_json"]) or {},
                    state_before_json=_load_json(row["state_before_json"]),
                    state_after_json=_load_json(row["state_after_json"]),
                )
            )
        return events
    finally:
        if owns_conn:
            conn.close()


def iter_events(session_id: str) -> Iterable[AuditEvent]:
    for event in fetch_events(session_id):
        yield event
