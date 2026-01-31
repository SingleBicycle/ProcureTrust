import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _load_app():
    repo_root = _repo_root()
    main_path = repo_root / "apps" / "api" / "main.py"
    spec = importlib.util.spec_from_file_location("procuretrust_api", main_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.app


def _load_audit():
    repo_root = _repo_root()
    audit_path = repo_root / "apps" / "api" / "services" / "audit.py"
    spec = importlib.util.spec_from_file_location("procuretrust_audit", audit_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_create_session_writes_audit(tmp_path, monkeypatch):
    db_path = tmp_path / "audit.db"
    monkeypatch.setenv("AUDIT_DB_PATH", str(db_path))

    client = TestClient(_load_app())
    response = client.post("/v1/sessions")
    assert response.status_code == 200
    session_id = response.json()["id"]

    audit = _load_audit()
    events = audit.fetch_events(session_id)
    assert any(event.event_type == "state_transition" for event in events)


def test_chat_writes_tool_calls_and_state(tmp_path, monkeypatch):
    db_path = tmp_path / "audit.db"
    monkeypatch.setenv("AUDIT_DB_PATH", str(db_path))

    client = TestClient(_load_app())
    session_id = client.post("/v1/sessions").json()["id"]

    response = client.post("/v1/chat", json={"session_id": session_id, "message": "Hello"})
    assert response.status_code == 200

    audit = _load_audit()
    events = audit.fetch_events(session_id)

    tool_events = [event for event in events if event.event_type == "tool_call"]
    assert len(tool_events) >= 2
    tool_names = {event.payload_json.get("tool") for event in tool_events}
    assert "CategoryResolver" in tool_names
    assert "AttributeExtractor" in tool_names

    state_events = [event for event in events if event.event_type == "state_transition"]
    assert any(event.state_before_json is not None for event in state_events)
    assert any(event.state_after_json is not None for event in state_events)


def test_replay_script_runs(tmp_path, monkeypatch):
    db_path = tmp_path / "audit.db"
    monkeypatch.setenv("AUDIT_DB_PATH", str(db_path))

    client = TestClient(_load_app())
    session_id = client.post("/v1/sessions").json()["id"]

    env = os.environ.copy()
    env["AUDIT_DB_PATH"] = str(db_path)
    result = subprocess.run(
        [sys.executable, "scripts/replay_session.py", session_id],
        cwd=str(_repo_root()),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert session_id in result.stdout or "state_transition" in result.stdout
