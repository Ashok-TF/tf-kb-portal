# Enterprise KB Platform — Execution Plan & Intuitive Design

**Feature #21: Enterprise Knowledge Base Platform**  
**Reference:** 6-step architecture walkthrough (Ingestion → Governance) + current portal template screenshots  
**Codebase:** `tf-kb-portal` (FastAPI + Next.js)

---

## 1. Executive summary

**v1 goal (6 weeks):** Deliver a working KB Portal where authorized users create KBs, upload documents, and ask questions in natural language — with **agentic search**, **grounded answers**, and **citations**. Covers backlog items **#1 (partial), #3 (partial), #4 (partial), #8 (partial), #9 (core)**.

**v2 (~8 weeks):** Enrichment (#6), artifacts (#5), wiki/graph (#7), governance (#10), SharePoint connector.

**v3 (~10 weeks):** Full pluggable search (#8), vision-LLM (#6), multi-connector framework (#10), advanced agentic fusion (#9).

---

## 2. Feature backlog → implementation map

| # | Feature | Priority | v1 | v2 | v3 | Current state |
|---|---------|----------|----|----|-----|---------------|
| 1 | **KB Portal** | P1 | Core UI + CRUD | Archive, tags, owner, search-provider config UI | TFGPT Desktop/Web integration APIs | Login, dashboard, KB detail, upload, doc table — **done** |
| 2 | **Access Management** | P1 | Single admin + placeholder roles | Admin / KB Manager / Consumer RBAC | Fine-grained permissions | Placeholder single-user auth only |
| 3 | **KB Registry** | P1 | Metadata in Postgres; agent reads name/desc/dept | Owner, status, tags, search config, processing stats | Agent-integration metadata | Basic `KnowledgeBase` model — **partial** |
| 4 | **Content Ingestion** | P1 | File upload + async pipeline | Website crawl + scheduled recrawl | HTML ingestion, connector sync | Upload + extract + chunk + embed — **done**; crawl **missing** |
| 5 | **Artifact Management** | P2 | — | URL registry + version history + agent URL answers | Full artifact lifecycle | **Not started** |
| 6 | **Enrichment Engine** | P1 | Basic text + OCR | LLM summaries, entities, relationships | Vision-LLM for diagrams | Text extract only — **partial** |
| 7 | **Knowledge Artifact Generation** | P2 | — | Auto wiki articles | Entities, relationships, knowledge graph | **Not started** |
| 8 | **Search & Retrieval Framework** | P1 | pgvector semantic + pluggable embedder/store abstractions | Hybrid BM25 + per-KB provider config | Graph/wiki/context strategies | Vector search API — **partial** |
| 9 | **Agentic Knowledge Search** | P1 | KB scoring + RAG + chat + citations | Multi-KB parallel + optional artifact/wiki | Full fusion + all strategies | Search API only; **no agent/chat** |
| 10 | **Security & Governance** | P1 | Per-KB vector namespace isolation | Audit log + authorized KB filtering | Analytics dashboard + SSO | Namespace isolation only — **minimal** |

### Key principles (design + engineering)

| Principle | v1 implementation | Later |
|-----------|-------------------|-------|
| **Knowledge isolation** | Vector namespace per KB; API scoped to KB id | RBAC filters registry + retrieval |
| **Pluggable by design** | `embeddings.py`, `vectorstore.py` interfaces; env-driven provider | Per-KB search provider in registry |
| **Semantic understanding** | Chunk + embed after text/OCR extract | Enrichment pipeline before index |
| **Agentic-first** | Chat API: discover KB → retrieve → answer + cite | Parallel multi-source `knowledge_search` |

### Open decisions (recommendations)

| Decision | Recommendation |
|----------|----------------|
| Default search provider per KB vs admin-selected | **Admin-selected at KB creation** with system default (pgvector); store in registry |
| Max KBs agent queries in parallel | **2–3** (configurable `AGENT_MAX_KBS=3`) |
| Artifact/wiki indexing mandatory per KB | **Optional flags** on KB: `index_artifacts`, `index_wikis` (default off in v1) |

---

## 3. Intuitive design system (portal template)

Your current portal screenshots define the **product UI language**. The architecture walkthrough uses a **separate dark presentation theme** for stakeholder demos — both belong in Figma as related but distinct tracks.

### 3.1 Portal design tokens (match existing code)

Based on [`frontend/src/app/globals.css`](../frontend/src/app/globals.css) and live screens:

| Token | Value | Usage |
|-------|-------|-------|
| Background | `oklch(0.985)` near-white | Page canvas |
| Card | White + `border` | All content panels |
| Primary | Near-black | CTA buttons, logo mark |
| Muted text | Gray ~56% | Department, timestamps, hints |
| Success | Green pill | `ready` status, doc counts |
| Warning | Amber | `processing` / `pending` |
| Destructive | Red | `failed`, delete confirm |
| Radius | `0.625rem` | Cards, inputs, buttons |
| Max width | `max-w-6xl` | Content column (header + main) |
| Font | System sans (antialiased) | Keep; optional: Inter in Figma |

**Brand mark:** Black rounded square `tf` + BookOpen icon + "KB Portal" — [`app-header.tsx`](../frontend/src/components/layout/app-header.tsx).

### 3.2 UX principles (intuitive flows)

1. **One primary action per screen** — Dashboard: "+ New Knowledge Base"; KB detail: upload zone; Chat: message input.
2. **Progressive disclosure** — Create KB form expands inline (already in template); advanced KB settings (search provider, tags) in edit drawer v2.
3. **Status at a glance** — Green `ready` badges, spinning loader for `processing`, red error under filename.
4. **Forgiving uploads** — Drag-drop + browse; show per-file queue and poll until ready (existing).
5. **Trust through sources** — Every AI answer shows expandable citation cards (filename, excerpt, score, KB name).
6. **Consistent actions** — View / Download on filename row; destructive actions (delete) require confirm.
7. **Wayfinding** — Breadcrumb: `← Knowledge Bases` → KB name → optional Chat tab.

### 3.3 Screen inventory (Figma + build)

#### Built today (template — keep & refine)

| Screen | Route | Key elements |
|--------|-------|--------------|
| Login | `/login` | Centered card, book icon, email/password, black Sign in |
| KB Dashboard | `/` | Header, grid of KB cards, inline create form, refresh + New KB |
| KB Detail | `/kb/[id]` | Back link, dept + doc count, upload card, documents table |

#### v1 screens to design & build

| Screen | Route | Intuitive layout |
|--------|-------|------------------|
| **KB Chat** | `/kb/[id]/chat` | Split or stacked: chat thread (left/top) + citations drawer (right/bottom on mobile). Sticky input: "Ask about this knowledge base…" |
| **Global Chat** | `/chat` | Same chat UI; header chip shows "Searching: HR Policies, Pre-sales KB" after agent selects KBs |
| **KB Settings** (minimal v1) | `/kb/[id]/settings` | Name, description, department, owner (read-only v1), processing summary |
| **Admin: Users & roles** (v2) | `/admin/access` | Table: user, role, assigned KBs |
| **Architecture demo** | `/demo` | Full-bleed dark walkthrough (Steps 01–06) — separate from portal chrome |

#### KB Detail — recommended v1 layout (intuitive upgrade)

```
┌─────────────────────────────────────────────────────────────┐
│ Header: tf KB Portal                    user · Sign out      │
├─────────────────────────────────────────────────────────────┤
│ ← HR Policies          [Documents] [Chat]     [Refresh]    │
│ Human Resources · 2 documents                                 │
├──────────────────────────┬──────────────────────────────────┤
│ Upload documents         │  Ask this knowledge base (v1)      │
│ [drop zone]              │  [chat input → opens /chat tab]  │
├──────────────────────────┴──────────────────────────────────┤
│ Documents                                                    │
│ Name (hover underline) [↓] | Status | Chunks | View | …     │
└─────────────────────────────────────────────────────────────┘
```

- **Tabs:** `Documents` | `Chat` — avoids cramming search + chat (search stays commented until folded into chat).
- **Chat tab** is the primary "ask questions" path (backlog #9).

### 3.4 Architecture walkthrough (Figma Track 2)

Dark theme from your 6 step screenshots — **not** the portal light theme:

| Frame | Title | Visual focus |
|-------|-------|--------------|
| Step 01 | Capture knowledge from anywhere | 3 source nodes → Content ingestion |
| Step 02 | Understand before you index | Vision-LLM enrichment pills |
| Step 03 | Turn content into reusable knowledge | Artifact grid → KB registry → domain KBs |
| Step 04 | Pluggable search, swappable storage | Provider pills + strategy stack |
| Step 05 | Agent reasons over merged knowledge | Query → agent → parallel searches → fusion → answer |
| Step 06 | Secure, audited, built to extend | Isolation, audit, analytics, connector cloud |

Shared chrome: step progress bar (1–6), legend (data flow / knowledge / agent), play controls.

---

## 4. Phased execution plan

### Phase 0 — Foundation (Week 1)

**Backend (Sreepad)**

| Task | Files / deliverable |
|------|---------------------|
| Docker Compose: Postgres + pgvector | `docker-compose.yml` |
| Schema: users, roles, kb_managers, chunks table | `backend/app/models.py`, Alembic migrations |
| Chunk persistence (provenance for citations) | `backend/app/services/pipeline.py` |
| OpenAI embedder + chat LLM abstraction | `backend/app/services/llm.py` (new) |
| Extend KB model: owner, status, tags, search_provider | `backend/app/models.py`, `schemas.py` |

**Frontend (Ashok)**

| Task | Files |
|------|-------|
| Design tokens doc in Figma | Figma file |
| App shell: nav links Home · Chat · Demo | `app-header.tsx` |
| KB card click → detail; polish create form | `page.tsx` |

**Acceptance:** Login works; KB CRUD on Postgres; Figma frames for login + dashboard + KB detail.

---

### Phase 1 — Ingestion hardening (Week 1–2) → Backlog #4

**Status:** ~80% done; close gaps.

| Task | Owner | Notes |
|------|-------|-------|
| Job queue (Redis/RQ or ARQ) instead of BackgroundTasks only | Backend | Retry failed jobs |
| HTML file type in allowlist | Backend | Backlog lists HTML |
| Reindex orphan vector cleanup | Backend | `pipeline.py` |
| Upload progress per file in UI | Frontend | `upload-zone.tsx` |
| Document view/download/preview | Frontend | **Done** |

**Acceptance:** Upload PDF/DOCX/PPTX/XLSX/image → `ready` with chunk count; failed shows reason.

---

### Phase 2 — Registry & access (Week 2–3) → Backlog #2, #3

| Task | Owner |
|------|-------|
| Users table + roles: `admin`, `kb_manager`, `consumer` | Backend |
| `kb_manager_assignments` junction table | Backend |
| API: list KBs filtered by role | Backend |
| Admin API: assign managers to KB | Backend |
| KB settings page (metadata edit) | Frontend |
| Manager sees only assigned KBs on dashboard | Frontend |

**Acceptance:** Manager A cannot open Manager B's KB (403). Admin sees all.

---

### Phase 3 — Search & RAG (Week 2–3) → Backlog #8 (partial), #9 (start)

| Task | Owner |
|------|-------|
| pgvector table + migration from local JSON | Backend |
| `POST /api/knowledge-bases/{id}/chat` — RAG + citations | Backend |
| Prompt template + citation extraction | Backend |
| Chat UI component (messages, streaming optional) | Frontend |
| Citation cards: filename, excerpt, score, view link | Frontend |
| KB detail **Chat** tab | Frontend |

**Acceptance:** Question in KB chat returns answer + ≥2 citations from uploaded docs.

---

### Phase 4 — Agentic search (Week 3–4) → Backlog #9 (core)

| Task | Owner |
|------|-------|
| KB scoring agent (name, description, department vs query) | Backend |
| `POST /api/chat` — global, auto-select 1–3 KBs | Backend |
| Parallel retrieval + fusion (dedup, re-rank, trim context) | Backend |
| Global chat page `/chat` | Frontend |
| KB badge on each citation | Frontend |

**Acceptance:** "Where is the AI sales deck?" routes to correct KB without user picking it.

---

### Phase 5 — Governance baseline (Week 4–5) → Backlog #10 (partial)

| Task | Owner |
|------|-------|
| Audit log table: upload, delete, search, chat, file access | Backend |
| Enforce KB access on all document/search/chat routes | Backend |
| Admin audit log viewer (simple table) | Frontend v2 |

**Acceptance:** Unauthorized KB returns 403; events written to audit_log.

---

### Phase 6 — Polish & demo (Week 5–6)

| Task | Owner |
|------|-------|
| Sample KBs + demo documents | Both |
| `/demo` architecture walkthrough page | Frontend |
| Figma: all v1 screens + 6 walkthrough frames | Design |
| E2E smoke test: login → upload → global chat | Both |
| RAG tuning (chunk size, top_k, prompt) | Backend |

**v1 success criteria (from backlog + deliverables):**

1. User logs in securely  
2. Creates 2+ KBs with metadata  
3. Uploads PDF/DOCX/PPTX successfully  
4. Documents reach `ready`  
5. Asks NL question in chat  
6. Agent selects correct KB(s)  
7. Answer grounded with 2+ citations  
8. Runs via Docker Compose  
9. `/demo` walkthrough available  

---

### v2 backlog (post–v1)

| Feature # | Focus |
|-----------|-------|
| 5 | Artifact registry (URL + metadata, version history) |
| 6 | LLM enrichment: summaries, entities, relationships |
| 7 | Wiki auto-generation |
| 8 | Hybrid search + per-KB provider UI |
| 10 | Full audit UI, usage analytics, SharePoint connector |

### v3 backlog

Vision-LLM (#6), knowledge graph (#7), Confluence/GitHub/Jira (#10), advanced parallel `knowledge_search` (#9).

---

## 5. API contract (v1 additions)

```
POST   /api/auth/login
GET    /api/knowledge-bases              # filtered by role
POST   /api/knowledge-bases
GET    /api/knowledge-bases/{id}
PATCH  /api/knowledge-bases/{id}         # metadata update
DELETE /api/knowledge-bases/{id}

GET    /api/knowledge-bases/{id}/documents
POST   /api/knowledge-bases/{id}/documents
GET    /api/documents/{id}/file

POST   /api/knowledge-bases/{id}/search  # existing vector search
POST   /api/knowledge-bases/{id}/chat    # NEW: RAG answer + citations

POST   /api/chat                         # NEW: global agentic chat

GET    /api/admin/users                  # v2
POST   /api/admin/kb/{id}/managers       # v2
GET    /api/admin/audit                  # v2
```

**Chat response shape (v1):**

```json
{
  "answer": "The latest AI sales deck is ...",
  "citations": [
    {
      "document_id": "...",
      "filename": "Enterprise_KB_OnePage_Summary.pdf",
      "kb_id": "...",
      "kb_name": "Pre-sales KB",
      "chunk_index": 0,
      "score": 0.82,
      "excerpt": "..."
    }
  ],
  "selected_kbs": [{ "id": "...", "name": "Pre-sales KB", "score": 0.91 }]
}
```

---

## 6. Data model extensions (v1)

```text
users (id, email, role, created_at)
kb_manager_assignments (user_id, kb_id)
knowledge_bases + owner_id, status, tags[], search_provider, index_artifacts, index_wikis
chunks (id, document_id, kb_id, chunk_index, text, char_start, char_end)  # for citations
audit_log (id, user_id, action, kb_id, document_id, metadata_json, created_at)
chat_sessions / chat_messages (optional v1.1)
```

---

## 7. Figma deliverable checklist

### Track A — Portal (light theme, match screenshots)

- [ ] Login  
- [ ] KB Dashboard (empty state)  
- [ ] KB Dashboard (with cards + create form open)  
- [ ] KB Detail — Documents tab  
- [ ] KB Detail — Chat tab (empty + with conversation)  
- [ ] Citation card component  
- [ ] Global Chat  
- [ ] Processing / failed / empty states  
- [ ] Mobile breakpoints (stacked layout)

### Track B — Architecture walkthrough (dark theme)

- [ ] Steps 01–06 (full-bleed frames)  
- [ ] Shared progress + legend components  

---

## 8. Demo script (stakeholder)

1. Open `/demo` — walk Steps 01 → 05 (2 min)  
2. Login → show KB Dashboard  
3. Open "HR Policies" → upload a PDF → watch status → `ready`  
4. Click filename → preview; download icon  
5. Switch to **Chat** tab → "What is our travel policy?"  
6. Show answer + citations → click citation to open source  
7. Go to **Global Chat** → "Where is the enterprise KB implementation doc?"  
8. Agent picks HR KB → grounded answer  

---

## 9. Gap summary: template today → v1 target

| Area | Today | v1 target |
|------|-------|-----------|
| Portal shell | Header only | + Chat nav, Demo link |
| KB metadata | Name, dept, description | + owner, status, tags, search config |
| KB detail | Upload + docs table | + Chat tab, tabs navigation |
| Search UI | Commented out | Replaced by Chat (agentic) |
| Auth | Single shared user | Multi-user + roles (min. manager scope) |
| AI | Vector search only | RAG chat + global agent |
| Storage | SQLite + local JSON | Postgres + pgvector |
| Governance | None | Audit log + access enforcement |

---

*Next step: share any additional feature notes or branding assets; then approve this plan to begin Phase 0 implementation and Figma build.*
