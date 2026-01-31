import importlib.util
from pathlib import Path

import pytest


def _load_state_machine():
    repo_root = Path(__file__).resolve().parents[3]
    module_path = repo_root / "apps" / "api" / "services" / "state_machine.py"
    spec = importlib.util.spec_from_file_location("procuretrust_state_machine", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_stage_enum_values():
    sm = _load_state_machine()
    assert [sm.Stage.A.value, sm.Stage.B.value, sm.Stage.C.value, sm.Stage.D.value] == [
        "A",
        "B",
        "C",
        "D",
    ]


def test_apply_patch_rejects_unknown_fields():
    sm = _load_state_machine()
    state = sm.SessionState(session_id="session-1")
    with pytest.raises(ValueError):
        sm.apply_patch(state, {"unknown": "value"})
    with pytest.raises(ValueError):
        sm.apply_patch(state, {"requirement_object": {"unknown_field": "value"}})


def test_plan_next_questions_structure():
    sm = _load_state_machine()
    state = sm.SessionState(session_id="session-1")
    missing = ["category_id", "quantity"]
    questions = sm.plan_next_questions(state, missing)
    assert len(questions) == 2
    for question in questions:
        assert isinstance(question, sm.Question)
        assert isinstance(question.field, str)
        assert isinstance(question.why, str)
        assert isinstance(question.prompt_template, str)
