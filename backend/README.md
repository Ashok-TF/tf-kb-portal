# KB Portal — Backend (FastAPI)

Ingestion + search API. Extracts text from uploaded files, chunks it, creates
embeddings, and stores vectors for semantic search.

## Run locally (zero external accounts)

```bash
cd backend
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env        # macOS/Linux: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/docs` for the interactive API (Swagger).

With the default `.env`, the app uses:
- **SQLite** for metadata (`./data/kb_portal.db`)
- a **local lexical embedder** (no API key)
- a **local JSON vector store** (`./data/vector_index.json`)

So it runs end-to-end with no Pinecone/OpenAI account.

## Switch to production providers

Edit `.env`:

```ini
EMBEDDING_PROVIDER=openai
OPENAI_API_KEY=sk-...

VECTOR_STORE=pinecone
PINECONE_API_KEY=...
PINECONE_INDEX=tfgpt-kb
PINECONE_REGION=us-east-1
```

Then `pip install openai pinecone` (already in requirements.txt) and restart.
The Pinecone index is auto-created on first use with the right dimension.

> Switching the embedding provider changes the vector dimension, so use a fresh
> Pinecone index / clear the local index when you change it.

## Image OCR

Image files (`.png`, `.jpg`, etc.) are OCR'd with Tesseract. Install the engine:
- Windows: `choco install tesseract` (or the UB-Mannheim installer)
- Linux: `apt-get install tesseract-ocr`
- macOS: `brew install tesseract`

If Tesseract isn't installed, image uploads fail with a clear message; all
other file types work without it.

## Supported file types

PDF, TXT, MD, CSV, JSON, DOCX, PPTX, XLSX, and images (PNG/JPG/etc. via OCR).
Legacy `.xls` is not supported — convert to `.xlsx`.

## API overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | Get a bearer token |
| GET | `/api/knowledge-bases` | List knowledge bases |
| POST | `/api/knowledge-bases` | Create a knowledge base |
| GET | `/api/knowledge-bases/{id}` | Get one |
| DELETE | `/api/knowledge-bases/{id}` | Delete + purge vectors |
| GET | `/api/knowledge-bases/{id}/documents` | List documents |
| POST | `/api/knowledge-bases/{id}/documents` | Upload a file (202, async) |
| GET | `/api/documents/{id}` | Document status |
| POST | `/api/documents/{id}/reindex` | Re-run the pipeline |
| DELETE | `/api/documents/{id}` | Delete a document |
| POST | `/api/knowledge-bases/{id}/search` | Semantic search |
