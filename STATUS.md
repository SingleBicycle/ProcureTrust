# STATUS.md — Build Snapshot (Auto-updated)

> DO NOT hand-edit inside the SNAPSHOT block.
> You can hand-edit sections outside SNAPSHOT.

## 0) Executive Summary (manual)
- Current milestone: Prompt 2 / 12
- Stage coverage: A [ ] B [ ] C [ ] D [ ]
- Demo status: P1 infra up (api/web/compose)
- Top risks / blockers:
  - Push/auth friction on remote env (mitigated via PAT / env-unset workaround)
  - Orchestration plan changed: remove LangGraph, adopt deterministic state machine

## 1) Completed Prompts (manual checklist)
- [x] P1 Infra
- [ ] P2 Schemas + Switch-to-StateMachine docs/snapshot
- [ ] P3 Audit (events + replay skeleton)
- [ ] P4 State Machine A/B (stage + ready gate)
- [ ] P5 Spec Engine (Spec Blocks + taxonomy + attribute graph v0)
- [ ] P6 Question Planner (top-1~3 info gain, state-driven)
- [ ] P7 RAG (knowledge packs + citations in audit trace)
- [ ] P8 KG-lite (deterministic rules: dependencies + risk triggers)
- [ ] P9 Web UX (completeness + missing list + rfq preview shell)
- [ ] P10 Images & Versioning (nano banana adapter + asset timeline)
- [ ] P11 Risk + RFQ (rules + templates + export)
- [ ] P12 Learning + Metrics + A->B Contract (tenant memory + metrics + reserved API)

## 2) Next Prompt Intent (manual)
- Next prompt number: P2
- Scope (allowed dirs/files):
  - PROJECT.md
  - STATUS.md
  - scripts/snapshot.py
  - packages/schemas/** (create)
  - apps/api/services/** (create state_machine skeleton + minimal tests)
  - apps/api/tests/** (add state_machine tests)
- DoD / acceptance commands:
  - make test
  - make snapshot
  - STATUS SNAPSHOT section no longer references LangGraph; shows StateMachine section
  - state_machine skeleton exists with tests passing

---

<!-- SNAPSHOT:BEGIN -->
## SNAPSHOT (auto)

### A) Git
- Branch: feat/p1-infra
- Last commit: cef6b99 feat: p1 infra fastapi+next+compose
- Dirty files: yes

### B) Repo Tree (key paths)
- apps/
  - api/
  - web/
    - pages/
    - Dockerfile
    - package.json
    - services/
    - tests/
    - Dockerfile
    - __init__.py
    - main.py
    - requirements.txt
- packages/
  - schemas/
    - requirement_object.schema.json
    - session_state.schema.json
    - tool_attribute_extractor.schema.json
    - tool_category_resolver.schema.json
- infra/
  - docker-compose.yml
- scripts/
  - snapshot.py

### C) API Surface (FastAPI)
- Base URL: (missing)
- Endpoints summary:
  - GET /health - Health
  - POST /v1/chat - Chat
  - POST /v1/sessions - Create Session
- Router files (fallback):
  - (missing)
- OpenAPI file path (if exported): (missing)

### D) State Machine Core (A/B/C/D)
- Module path: apps/api/services/state_machine.py
- Stage enum found: yes (apply_patch: yes, compute_missing: yes)
- Ready gate rules present: no
- Category registry count: 0
- Next-question planner present: yes

### E) Schemas
- RequirementObject version: https://procuretrust.ai/schemas/requirement_object.v0.schema.json
- schema.json path: packages/schemas/requirement_object.schema.json
- Top-level fields (first 30):
  - version
  - category_id
  - quantity
  - timeline
  - shipping
  - packaging
  - branding
  - compliance
  - design_brief
- Required fields:
  - version

### F) DB / Migrations
- DB tables (best-effort):
  - (missing)
- Latest migrations:
  - (missing)

### G) RAG / KG-lite
- Vector store locations:
  - (missing)
- Knowledge packs:
  - (missing)
- KG-lite rules:
  - (missing)

### H) Frontend Modules
- Pages/routes:
  - apps/web/pages/index.js
- Key UI components present:
  - Chat: (missing)
  - CompletenessBar: (missing)
  - MissingList: (missing)
  - RFQPreview: (missing)
  - AssetTimeline: (missing)

### I) Tests & Commands
- make dev: yes
- make test: yes
- make snapshot: yes
- pytest config: (missing)
- package.json test script: yes (apps/web/package.json)
- CI workflows:
  - (missing)
- Suggested commands:
  - make snapshot
  - make dev
  - make test

### J) Known Issues (auto-collected TODO markers)
- TODO/FIXME list (top 20):
  - prompt_studio.txt:264: TODO markers)
  - prompt_studio.txt:265: TODO/FIXME list (top 20):
<!-- SNAPSHOT:END -->

---

## 3) Manual Notes (manual)
- Product decisions taken:
  - Switched orchestration from LangGraph to deterministic state machine + 2 LLM tools (category + attribute)
- UX copy changes:
- Prompt changes / learnings:
  - Always unset VSCode git askpass env for pushes in remote env when needed
