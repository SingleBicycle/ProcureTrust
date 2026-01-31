from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Stage(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class RequirementObject(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str = "v0"
    category_id: Optional[str] = None
    quantity: Optional[Dict[str, Any]] = None
    timeline: Optional[Dict[str, Any]] = None
    shipping: Optional[Dict[str, Any]] = None
    packaging: Optional[Dict[str, Any]] = None
    branding: Optional[Dict[str, Any]] = None
    compliance: Optional[Dict[str, Any]] = None
    design_brief: Optional[Dict[str, Any]] = None


class Question(BaseModel):
    model_config = ConfigDict(extra="forbid")

    field: str
    why: str
    prompt_template: str


class SessionState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    stage: Stage = Stage.A
    current_category_id: Optional[str] = None
    requirement_object: RequirementObject = Field(default_factory=RequirementObject)
    assets_index: List[Dict[str, Any]] = Field(default_factory=list)


CATEGORY_REGISTRY: Dict[str, Dict[str, Any]] = {}

REQUIRED_FIELDS = (
    "category_id",
    "quantity",
    "timeline",
    "shipping",
    "packaging",
    "branding",
    "compliance",
    "design_brief",
)

ALLOWED_PATCH_TOP_LEVEL = {
    "stage",
    "current_category_id",
    "requirement_object",
    "assets_index",
}

QUESTION_WHY = {
    "category_id": "Locks the category so specs and risks stay accurate.",
    "quantity": "Impacts MOQ, pricing tiers, and supplier feasibility.",
    "timeline": "Sets delivery feasibility and production planning.",
    "shipping": "Affects landed cost, lead time, and compliance handling.",
    "packaging": "Determines carton specs and labeling needs.",
    "branding": "Clarifies logo/brand placement and IP constraints.",
    "compliance": "Ensures required standards and labeling are captured.",
    "design_brief": "Guides design assets and product positioning.",
}

QUESTION_TEMPLATES = {
    "category_id": "What product category should we lock in?",
    "quantity": "What is your estimated order quantity?",
    "timeline": "What is your target delivery timeline?",
    "shipping": "Do you have shipping preferences or destinations?",
    "packaging": "What packaging requirements do you have?",
    "branding": "What branding or logo requirements should we include?",
    "compliance": "Are there compliance standards or certifications required?",
    "design_brief": "Please share a short design brief or aesthetic goals.",
}


def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip().lower() in {"", "unknown", "tbd", "n/a"}
    if isinstance(value, (list, tuple, dict)):
        return len(value) == 0
    return False


def apply_patch(state: SessionState, patch: Dict[str, Any]) -> SessionState:
    if not isinstance(patch, dict):
        raise ValueError("patch must be a dict")

    unknown_top = set(patch) - ALLOWED_PATCH_TOP_LEVEL
    if unknown_top:
        raise ValueError(f"Unknown patch fields: {sorted(unknown_top)}")

    updates: Dict[str, Any] = {}

    if "stage" in patch:
        stage_value = patch["stage"]
        updates["stage"] = stage_value if isinstance(stage_value, Stage) else Stage(str(stage_value))

    if "current_category_id" in patch:
        updates["current_category_id"] = patch["current_category_id"]

    if "assets_index" in patch:
        assets = patch["assets_index"]
        if not isinstance(assets, list):
            raise ValueError("assets_index must be a list")
        updates["assets_index"] = assets

    if "requirement_object" in patch:
        ro_patch = patch["requirement_object"]
        if not isinstance(ro_patch, dict):
            raise ValueError("requirement_object patch must be a dict")
        allowed_ro = set(RequirementObject.model_fields.keys())
        unknown_ro = set(ro_patch) - allowed_ro
        if unknown_ro:
            raise ValueError(f"Unknown requirement_object fields: {sorted(unknown_ro)}")
        updates["requirement_object"] = state.requirement_object.model_copy(update=ro_patch)

    return state.model_copy(update=updates)


def compute_missing(state: SessionState) -> List[str]:
    missing: List[str] = []
    for field in REQUIRED_FIELDS:
        value = getattr(state.requirement_object, field, None)
        if _is_missing_value(value):
            missing.append(field)
    return missing


def plan_next_questions(state: SessionState, missing: List[str]) -> List[Question]:
    _ = state
    questions: List[Question] = []
    for field in missing[:3]:
        why = QUESTION_WHY.get(field, "Required to complete the RFQ accurately.")
        prompt = QUESTION_TEMPLATES.get(field, f"Please provide {field}.")
        questions.append(Question(field=field, why=why, prompt_template=prompt))
    return questions
