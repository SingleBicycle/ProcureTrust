from __future__ import annotations

from enum import Enum
from typing import Any, Dict

from pydantic import BaseModel, ConfigDict, Field


class Stage(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class SessionState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    stage: Stage = Stage.A
    requirement_object: Dict[str, Any] = Field(default_factory=dict)


ALLOWED_PATCH_FIELDS = {"stage", "requirement_object"}


def apply_patch(state: SessionState, patch: Dict[str, Any]) -> SessionState:
    if not isinstance(patch, dict):
        raise ValueError("patch must be a dict")
    unknown = set(patch) - ALLOWED_PATCH_FIELDS
    if unknown:
        raise ValueError(f"Unknown patch fields: {sorted(unknown)}")
    updates: Dict[str, Any] = {}
    if "stage" in patch:
        stage_value = patch["stage"]
        updates["stage"] = stage_value if isinstance(stage_value, Stage) else Stage(str(stage_value))
    if "requirement_object" in patch:
        value = patch["requirement_object"]
        if not isinstance(value, dict):
            raise ValueError("requirement_object patch must be a dict")
        updates["requirement_object"] = value
    return state.model_copy(update=updates)
