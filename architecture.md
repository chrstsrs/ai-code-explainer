# Architecture

- Dev: 3 services → `frontend` (React dev server) + `backend` (Django) + `db` (Postgres).
- Prod: 3 services → `nginx` (serves SPA, proxies /api) + `backend` (Gunicorn/Uvicorn) + `db`.
- AI: adapter pattern in `backend/app/ai/` with a `MockLLMClient` by default.

Request Flow (prod):
Browser → Nginx (serves / and static) → /api/* → Django → LLM adapter → Response
