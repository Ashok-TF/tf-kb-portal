# ThoughtFocus KB Portal

A self-contained, department-facing **knowledge base portal**. Users sign in,
create a knowledge base per department, upload files from their local machine
(PDF, TXT, images, PPTX, XLSX, DOCX, CSV, MD), and the system automatically
**extracts text → chunks → embeds → stores vectors** so the content becomes
semantically searchable.

It runs **out of the box with no external accounts**, and flips to
**OpenAI embeddings + Pinecone** by changing a few environment variables.

```
tf-kb-portal/
├── backend/     FastAPI service: ingestion pipeline + search API
└── frontend/    Next.js portal: login, knowledge bases, upload, search
```

## Architecture at a glance

```
Browser (Next.js)
   │  login → bearer token (localStorage)
   │  upload file ─────────────► POST /api/.../documents  (HTTP 202, async)
   ▼
FastAPI backend
   ├─ extract text   (pypdf / python-docx / python-pptx / openpyxl / OCR …)
   ├─ chunk          (~900 chars, 150 overlap)
   ├─ embed          (fake lexical  | OpenAI)
   └─ upsert vectors (local JSON    | Pinecone)   namespace = "kb-<id>"
                                   ▲
   search query ──► embed ──► vector store .query() ──► ranked chunks
```

Metadata (knowledge bases, documents, status) lives in SQL (SQLite by default,
Postgres supported). Vectors live in the vector store.

## Quick start (two terminals)

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1          # Windows PowerShell
pip install -r requirements.txt
copy .env.example .env              # cp on macOS/Linux
uvicorn app.main:app --reload --port 8000
```

Backend runs at `http://localhost:8000` (Swagger UI at `/docs`).

### 2. Frontend

```bash
cd frontend
npm install
copy .env.local.example .env.local  # cp on macOS/Linux
npm run dev
```

Portal runs at **`http://localhost:3001`**.

### 3. Sign in

Default credentials (set in `backend/.env`):

- Email: `admin@thoughtfocus.com`
- Password: `tfKB@123`

## How to use

1. **Sign in** at `http://localhost:3001`.
2. Click **New Knowledge Base**, name it (e.g. *HR Policies*), set a department.
3. Open the knowledge base and **drag-and-drop files** into the upload zone.
   Each file shows a status: `pending → processing → ready` (the page polls
   automatically). `failed` shows the reason.
4. Use the **Search** box to run a semantic query and see the most relevant
   chunks, ranked by score, with their source file.
5. Use the row actions to **reindex** or **delete** a document.

## Going to production

| Concern | Default (dev) | Production |
|---------|---------------|------------|
| Embeddings | local lexical (`fake`) | `EMBEDDING_PROVIDER=openai` + `OPENAI_API_KEY` |
| Vectors | local JSON file | `VECTOR_STORE=pinecone` + `PINECONE_API_KEY` |
| Metadata DB | SQLite | `DATABASE_URL=postgresql+psycopg://…` |
| Auth | single shared login | wire SSO/Azure AD into `backend/app/auth.py` |

See `backend/README.md` for details (including Tesseract OCR setup for images).

## Notes / next steps

- Auth is intentionally a simple placeholder (one shared credential). The token
  is a signed HMAC; swap `app/auth.py` for real SSO when ready.
- Multi-tenant department isolation, per-user access control, and audit logging
  are natural next additions (the existing `tfGPT-Admin` KB schema is a good
  reference for a richer model).
- `.xls` (legacy Excel) isn't supported — convert to `.xlsx`.
