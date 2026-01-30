# STATUS.md — Build Snapshot (Auto-updated)

> DO NOT hand-edit inside the SNAPSHOT block.
> You can hand-edit sections outside SNAPSHOT.

## 0) Executive Summary (manual)
- Current milestone: Prompt __ / 12
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
- Next prompt number:
- Scope (allowed dirs/files):
- DoD / acceptance commands:

---

<!-- SNAPSHOT:BEGIN -->
## SNAPSHOT (auto)

### A) Git
- Branch: main
- Last commit: 31700c3 Add comprehensive .gitignore file
- Dirty files: yes

### B) Repo Tree (key paths)
- apps/ (missing)
- packages/ (missing)
- infra/ (missing)
- scripts/
  - snapshot.py

### C) API Surface (FastAPI)
- Base URL: (missing)
- Endpoints summary:
  - (missing)
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
  - (missing)
- Key UI components present:
  - Chat: (missing)
  - CompletenessBar: (missing)
  - MissingList: (missing)
  - RFQPreview: (missing)
  - AssetTimeline: (missing)

### I) Tests & Commands
- make dev: no
- make test: no
- make snapshot: yes
- pytest config: (missing)
- package.json test script: (missing)
- CI workflows:
  - (missing)
- Suggested commands:
  - make snapshot

### J) Known Issues (auto-collected TODO markers)
- TODO/FIXME list (top 20):
  - (missing)
<!-- SNAPSHOT:END -->

---

## 3) Manual Notes (manual)
- Product decisions taken:
- UX copy changes:
- Prompt changes / learnings:
