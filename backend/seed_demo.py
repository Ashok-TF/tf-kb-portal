"""Seed demo knowledge bases and upload sample documents."""

import io
import time
from pathlib import Path

import httpx

BASE = "http://localhost:8000"
DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"

SAMPLES = [
    ("HR Policies", "Human Resources", "HR policies and confidential documents"),
    ("Pre-sales", "Sales", "Sales decks and one-pagers"),
]

FILES = [
    "Enterprise-KB-Platform-v1-Implementation.docx",
    "Enterprise_KB_OnePage_Summary.pdf",
]


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=120) as c:
        token = c.post(
            "/api/auth/login",
            json={"email": "admin@thoughtfocus.com", "password": "tfKB@123"},
        ).json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        for name, dept, desc in SAMPLES:
            existing = c.get("/api/knowledge-bases", headers=headers).json()
            match = next((k for k in existing if k["name"] == name), None)
            if match:
                kb_id = match["id"]
                print(f"KB exists: {name}")
            else:
                kb = c.post(
                    "/api/knowledge-bases",
                    headers=headers,
                    json={"name": name, "description": desc, "department": dept},
                ).json()
                kb_id = kb["id"]
                print(f"Created KB: {name}")

            for fname in FILES:
                path = DOCS_DIR / fname
                if not path.is_file():
                    print(f"  skip missing {fname}")
                    continue
                docs = c.get(f"/api/knowledge-bases/{kb_id}/documents", headers=headers).json()
                if any(d["filename"] == fname for d in docs):
                    print(f"  already uploaded {fname}")
                    continue
                content = path.read_bytes()
                up = c.post(
                    f"/api/knowledge-bases/{kb_id}/documents",
                    headers=headers,
                    files={"file": (fname, io.BytesIO(content), "application/octet-stream")},
                )
                print(f"  uploaded {fname}: {up.status_code}")

            for _ in range(30):
                docs = c.get(f"/api/knowledge-bases/{kb_id}/documents", headers=headers).json()
                if docs and all(d["status"] in {"ready", "failed"} for d in docs):
                    break
                time.sleep(2)

        print("\nDemo seed complete.")


if __name__ == "__main__":
    main()
