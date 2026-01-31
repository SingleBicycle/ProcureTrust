import importlib.util
from pathlib import Path

import pytest


pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient


def _load_app():
    repo_root = Path(__file__).resolve().parents[3]
    main_path = repo_root / "apps" / "api" / "main.py"
    spec = importlib.util.spec_from_file_location("procuretrust_api", main_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.app


def test_health():
    client = TestClient(_load_app())
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_create_session():
    client = TestClient(_load_app())
    response = client.post("/v1/sessions")
    assert response.status_code == 200
    payload = response.json()
    assert "id" in payload
