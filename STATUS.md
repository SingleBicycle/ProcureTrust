# STATUS.md — Build Snapshot (Auto-updated)

> DO NOT hand-edit inside the SNAPSHOT block.
> You can hand-edit sections outside SNAPSHOT.

## 0) Executive Summary (manual)
- Current milestone: Prompt 1 / 12
- Stage coverage: A [ ] B [ ] C [ ] D [ ]
- Demo status: (what works end-to-end)
- Top risks / blockers:

## 1) Completed Prompts (manual checklist)
- [ ] P1 Infra
- [ ] P2 Schemas
- [ ] P3 Audit
- [ ] P4 Orchestrator A/B
- [ ] P5 Spec Engine
- [ ] P6 Question Planner
- [ ] P7 RAG
- [ ] P8 KG-lite
- [ ] P9 Web UX
- [ ] P10 Images & Versioning
- [ ] P11 Risk + RFQ
- [ ] P12 Learning + Metrics + A->B Contract

## 2) Next Prompt Intent (manual)
- Next prompt number: P1
- Scope (allowed dirs/files): packages/schemas, apps/api(schema integration)
- DoD / acceptance commands: schema.json 生成 + patch merge tests + make test + make snapshot

---

<!-- SNAPSHOT:BEGIN -->
## SNAPSHOT (auto)

### A) Git
- Branch: feat/p1-infra
- Last commit: 48b802e chore: add project/status + snapshot tooling
- Dirty files: yes

### B) Repo Tree (key paths)
- apps/
  - api/
  - web/
    - pages/
    - Dockerfile
    - package.json
    - tests/
    - Dockerfile
    - __init__.py
    - main.py
    - requirements.txt
- packages/ (missing)
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

### D) Orchestrator Graph (LangGraph)
- Graph module: (missing)
- Nodes:
  - (missing)
- Edges:
  - (missing)
- Stage machine support:
  - stage values found:
    - (missing)
  - ready gate: (missing)

### E) Schemas
- RequirementObject version: (missing)
- schema.json path: (missing)
- Top-level fields (first 30):
  - (missing)
- Required fields:
  - (missing)

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
- UX copy changes:
- Prompt changes / learnings:
