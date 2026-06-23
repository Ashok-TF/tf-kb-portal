"""Quick end-to-end smoke test against a running backend on localhost:8000."""

import io
import time

import httpx

BASE = "http://localhost:8000"


def main() -> None:
    with httpx.Client(base_url=BASE, timeout=30) as c:
        print("health:", c.get("/health").json())

        token = c.post(
            "/api/auth/login",
            json={"email": "admin@thoughtfocus.com", "password": "tfKB@123"},
        ).json()["token"]
        headers = {"Authorization": f"Bearer {token}"}
        print("login: OK")

        kb = c.post(
            "/api/knowledge-bases",
            headers=headers,
            json={"name": "Smoke Test KB", "department": "QA", "description": "e2e"},
        ).json()
        kb_id = kb["id"]
        print("created kb:", kb_id)

        content = (
            "ThoughtFocus builds AI knowledge portals. Pinecone stores vector "
            "embeddings for semantic search. The project uses retrieval augmented "
            "generation to answer employee questions across departments."
        ).encode()
        up = c.post(
            f"/api/knowledge-bases/{kb_id}/documents",
            headers=headers,
            files={"file": ("sample.txt", io.BytesIO(content), "text/plain")},
        )
        print("upload status:", up.status_code, "->", up.json()["status"])

        for _ in range(15):
            time.sleep(1)
            docs = c.get(f"/api/knowledge-bases/{kb_id}/documents", headers=headers).json()
            st = docs[0]["status"]
            if st in {"ready", "failed"}:
                print("processing finished:", st, "chunks:", docs[0]["chunk_count"])
                if st == "failed":
                    print("error:", docs[0]["error"])
                break
        else:
            print("still processing after timeout")

        res = c.post(
            f"/api/knowledge-bases/{kb_id}/search",
            headers=headers,
            json={"query": "vector embeddings semantic search", "top_k": 3},
        ).json()
        print("search matches:", len(res["matches"]))
        for m in res["matches"]:
            print(f"  score={m['score']:.3f} {m['filename']}: {m['text'][:60]}...")

        c.delete(f"/api/knowledge-bases/{kb_id}", headers=headers)
        print("cleanup: deleted kb")
        print("\nSMOKE TEST PASSED")


if __name__ == "__main__":
    main()
