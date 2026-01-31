# PROJECT.md — A-side Procurement Requirements Convergence Platform (US Buyer)

> Single source of truth for architecture, contracts, and guardrails.
> Read this FIRST before making changes.

## 0. Product Goal (MVP: A-side closed loop)
We build a web platform for US buyers to converge procurement requirements via:
- Chat (text) + reference image upload
- AI image generation/editing (nano banana preferred) with version traceability
- Output: structured RequirementObject (JSON Schema) + Design Asset Pack + RFQ (EN primary, CN appendix optional)
- Future B-side: RFQ -> 1688/Taobao sourcing & quote automation (NOT in MVP; only reserve interfaces)

MVP success criteria:
- User can complete Stage A/B/C/D without human intervention and export a usable RFQ.
- Every state change is auditable and replayable.
- Category-specific dynamic fields work for at least 3 representative categories (shoes / infant formula / restaurant plates).

## 1. Non-goals (for MVP)
- Full taxonomy coverage of all product categories (use 80/20 + fallback).
- Full B-side automation (only schema + endpoint contract).
- Complex image editing UX (start with generate -> select -> text-edit; optional region edit later).

## 2. Core Experience: “Human buyer agent” rhythm
Every assistant turn MUST contain:
1) WHY I’m asking (quote-impact / compliance / logistics reason)
2) WHAT I’ve captured (recap snapshot)
3) WHAT’s next (next step + remaining missing count)

Never ask 30 questions at once. Ask 1–3 high-information questions per turn.

## 3. Orchestrator: Deterministic Stage Machine (A/B/C/D) + Ready Gate
We do NOT use LangGraph in MVP. The orchestrator is a deterministic state machine.

Stages:
- Stage A: Category & goal lock (category, usage, target market=US, rough qty, ref image?)
- Stage B: Spec convergence (dynamic fields per category, slot filling)
- Stage C: Design asset finalization (generate -> choose -> edit -> lock)
- Stage D: RFQ + risk confirmation (risk engine + user confirms required actions; export)

Ready Gate rules:
- Cannot proceed to next stage unless schema + required fields satisfied for the stage.
- Stage D finalize requires: missing_fields == 0 AND required risk actions confirmed.

Implementation note:
- `apps/api/services/state_machine.py` is the brain (rules + transitions + missing + next questions).
- LLM is used ONLY as tools:
  - CategoryResolver: normalize category / detect switch
  - AttributeExtractor: extract structured patch updates (NO free-form decisions)

## 4. Key Data Contracts (Do not break)
### 4.1 RequirementObject (JSON Schema)
- Stored as canonical source of truth.
- Updates are PATCH-style (diff) only; never overwrite blindly.
- Must not hallucinate: unknown fields remain null / "unknown" and trigger questions.
- Schema versioning: `requirement_object.version` increments only when schema changes.

### 4.2 State Machine State (SessionState)
State is stored server-side and is replayable:
- session_id
- stage (A/B/C/D)
- current_category_id (+ optional subcategory_hint)
- requirement_object (json, validated)
- missing_fields (computed, not authoritative)
- next_questions (computed, not authoritative)
- risk_flags / required_actions (computed)
- assets_index (ids + pointers)
- audit_cursor / last_event_id

### 4.3 Audit Events
Every state mutation must emit an audit event:
- user_message / assistant_message
- tool_call (category / attribute / retrieval / image)
- state_before / state_after
- node_error
- retrieval_trace (RAG query + doc ids)
- image_event (generate/edit/select)
Audit must enable replay.

### 4.4 Asset Versioning
Asset record must include:
- asset_id, parent_id, kind(upload/generate/edit), prompt, params, provider, url, created_at
- user selection reason
Version tree must be reconstructable.

### 4.5 A->B Contract (Reserved)
RFQSubmission schema:
- rfq_id
- requirement_object (json)
- assets (urls + metadata)
- rfq_document (html + optional pdf)
- created_at
B-side response:
- ack + optional recommendations list

## 5. Category Spec Engine (Dynamic fields)
We DO NOT create a full taxonomy manually.
We implement:
- Taxonomy (small top-level categories)
- Spec Blocks (reusable modules, ~20–40 blocks)
- Attribute Graph (dependencies: if A then require B)
- Template/Question library (field explanation, examples, question templates, RFQ line templates)

Fallback for long tail:
- Map to nearest top-level category -> pick common blocks via RAG -> LLM drafts a temporary field graph
- Must pass schema + risk validation
- UI must disclose: "Temporary spec list; high-risk gaps remain"

## 6. RAG + KG-lite integration
RAG knowledge packs (priority):
- category spec guides (fields, units, pitfalls)
- compliance & labeling guides (US-focused)
- materials/process & cost impact
- procurement talk tracks + RFQ templates

KG-lite responsibilities (deterministic rules):
- field dependency activation
- missing-field impact ranking
- risk triggers (kids/food/food-contact/battery/liquid/etc.)

## 7. Learning (Controlled)
- L1 Session memory: per-session captured facts; avoid repeated questions
- L2 Tenant memory: organization defaults (Incoterms, destination ZIP, packaging preference, sizing system)
- L3 Offline improvement: analytics from real conversations to refine rules/prompts (NO online self-modifying logic)

## 8. Tech Stack (default)
- Backend: FastAPI (Python) + deterministic state machine orchestrator
- DB: Postgres (jsonb) + optional pgvector
- Cache/Queue: Redis
- Assets: S3-compatible storage
- Frontend: Next.js (React)
- Observability: structured logs + traces + metrics endpoints

## 9. Repo Structure (monorepo)
- apps/api              # FastAPI + state_machine + services (audit, rfq, images)
- apps/web              # Next.js UI
- packages/schemas      # shared schema + codegen (RequirementObject, SessionState, RFQSubmission)
- scripts/              # snapshot, tooling
- infra/                # docker, deploy

## 10. Engineering Rules (PR discipline)
- Small PRs only, aligned with staged prompts.
- Each PR must update STATUS.md via snapshot script.
- Never break existing API contracts.
- Add tests for:
  - schema validation
  - patch merge
  - state machine transitions (A/B/C/D)
  - question planner (top-k)
  - risk triggers
  - asset version chain

Hard guardrails for IDE agents / Codex:
1) Before coding, print a 5-line summary of constraints read from PROJECT.md/STATUS.md.
2) If you believe refactoring is required, STOP; do not refactor. Output the minimal change list instead.

## 11. Local Dev Commands (expected)
- make dev
- make test
- make snapshot
- docker compose up

## 12. References (internal)
See research report PDF for requirements and rationale.
