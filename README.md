# Multiple LLMs, AI Code Explainer (Django + React + Nginx)

> A code explainer on Django + React using LLM/AI.  
> Dev: React dev server + Django API + Postgres.  
> Prod: Nginx serves built SPA, proxies `/api/*` → Django (Gunicorn/Uvicorn) + Postgres.

---

## What this project does
- **Explain code snippets** (Python/JS) using an AI adapter layer.
- **Guess algorithmic complexity (Big-O)** and provide reasoning.
- **Generate starter unit tests** (pytest) for the snippet.
- **Run multiple LLMs on the same snippet** and compare their answers.
- **Score each LLM response** in a range of **[-100, 100]**, with optional comments.
- **Review history of snippets and runs** (recent snippets list).


I is designed with clean separation between **frontend** and **backend**. 
To run it properly requires one or more LLM API keys.

---

## Repository structure
```
/
├─ frontend/                     # React SPA (dev server in dev; built assets in prod)
│  ├─ public/
│  └─ src/
├─ backend/                      # Django + DRF API
│  └─ app/
│     ├─ server/                 # Django project
│     ├─ api/                    # API app
│     └─ ai/                     # LLM adapters
├─ infra/                        # Dockerfiles, Compose, Nginx config
│  ├─ compose/
│  ├─ docker/
│  └─ nginx/
├─ architecture.md
└─ README.md
```

---

## Architecture
- **Development (3 services)**  
  - `frontend`: React dev server (HMR)  
  - `backend`: Django (autoreload)  
  - `db`: Postgres

- **Production (3 services)**  
  - `nginx`: serves SPA and proxies `/api/*`  
  - `backend`: Django via Gunicorn/Uvicorn  
  - `db`: Postgres

Request flow (prod):  
**Browser → Nginx (static SPA) → /api/* → Django (DRF) → AI adapter → Response**

---

## Prerequisites
- Docker & Docker Compose
- No AI key required for the mock provider.

---

## Quickstart

### Development
```
cd infra/compose
docker compose -f docker-compose.dev.yml up --build
# Frontend: http://localhost:3000
# API:      http://localhost:8000/api/v1/explain/
```

### Production (local)
```
cd infra/compose
docker compose -f docker-compose.prod.yml up --build
# Visit: http://localhost/  (Nginx serves SPA, proxies /api/)
```

---

## Environment configuration
- **Backend env (shared in Compose):**
  - `POSTGRES_*`: DB connection
  - `CORS_ALLOWED_ORIGINS`: origins separated by commas
  - `AI_PROVIDER`: `mock` (default) | `openai` | `anthropic` | `ollama` (more may be added)
  - `AI_MODEL`: model name (used by real providers)
  - `AI_API_KEY`: provider key (needed only when switching off `mock`)
- **Frontend env**  
  - `REACT_APP_API_URL` (dev): defaults to `http://localhost:8000/api`

Use `.env` template and inject at runtime.

---

## API (contract-first)

### **Create Snippet**
**POST** `/api/v1/snippets/`

Request:
```
{ "language": "python", "code": "def add(a,b): return a+b", "options": { "tests": true } }
```

### **Run Snippet on a Model**
**POST** `/api/v1/runs/`

Request:
```
{ "snippetId": 1, "modelId": 2 }
```

Response:
```
{
  "id": 10,
  "status": "ok",
  "response_text": "Adds two numbers.",
  "complexity_time": "O(1)",
  "complexity_space": "O(1)",
  "complexity_reasoning": "Simple return statement.",
  "latency_ms": 210
}
```

### **Upsert Feedback**
**POST** `/api/v1/feedback/`

Request:
```
{ "run": 10, "score": -10, "comment": "Too simplistic" }
```

Response:
```
{ "run": 10, "score": -10, "comment": "Too simplistic" }
```
---

## AI adapter design
- `backend/app/ai/` houses a **provider-agnostic interface** (`get_llm_client()`).
- Default is `MockLLMClient` for instant local runs (no keys).
- Add providers (e.g., `openai.py`) and switch via `AI_PROVIDER` env var.
- Multiple models are supported; each run links a **Snippet** to an **LLMModel**.

---

## Scoring & History
- Every run stores the model’s output, complexity estimates, and status.
- Users can **score responses in [-100, 100]** and add comments.
- Scores are saved in the DB (one feedback per run).
- A **Recent Snippets** list allows reviewing prior snippets and their runs.

---

## Testing
- **Backend:** `pytest` with a fake LLM client for deterministic responses. Run from inside the backend app folder:
```commandline
cd /srv/backend/app
pytest ..
```
- **Frontend:** basic component test for the form + API client mock. Run from inside the frontend folder (container or host):
```commandline
cd frontend
npm test
```
---

## License
MIT
