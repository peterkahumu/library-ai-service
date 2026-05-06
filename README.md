# AI Service

A FastAPI microservice that powers the **LibraBot** chatbot and book recommendation engine for the Library Management System.

## Architecture Overview

This service runs as an independent microservice within the `bsc-project` monorepo. It communicates with the main Django application (`library-management/`) over HTTP and is orchestrated alongside the other services via the root `docker-compose.yml`.

```
bsc-project/
├── ai_service/          ← you are here
│   ├── main.py          # FastAPI application
│   ├── Dockerfile
│   ├── requirements.txt
│   └── docker-compose.yml  # standalone compose (dev only)
├── library-management/  # Django app (consumes this service)
└── docker-compose.yml   # full-stack orchestration
```

## Endpoints

### `GET /health`

Health check probe used by orchestration tooling.

**Response:**

```json
{ "status": "healthy" }
```

---

### `POST /chat/stream`

Streams an AI-generated chat response via **Server-Sent Events (SSE)**.

**Request body:**

```json
{
  "messages": [
    { "role": "user", "content": "How do I borrow a book?" }
  ]
}
```

**SSE events:**

| Event     | Payload                          | Description                  |
|-----------|----------------------------------|------------------------------|
| `message` | `{ "content": "..." }`          | Incremental response chunk   |
| `error`   | `{ "error": "..." }`            | Error message                |
| `done`    | `{ "done": true }`              | End-of-stream sentinel       |

---

### `POST /recommend`

Returns book recommendations based on a user's borrowing history *(stub — to be expanded)*.

**Request body:**

```json
{
  "user_id": 1,
  "history": ["978-0-13-468599-1"]
}
```

**Response:**

```json
{
  "status": "success",
  "recommendations": [
    { "title": "The Great Gatsby", "reason": "Classic literature" },
    { "title": "1984", "reason": "Dystopian classic" },
    { "title": "To Kill a Mockingbird", "reason": "Highly rated" }
  ]
}
```

## Environment Variables

| Variable        | Required | Description                                    |
|-----------------|----------|------------------------------------------------|
| `OPENAI_API_KEY`| Yes      | OpenAI API key for chat completions            |
| `SYSTEM_PROMPT` | No       | Override the default LibraBot system prompt     |

Copy and edit the example env file:

```bash
cp .env_example .env
```

## Running Locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The service will be available at `http://localhost:8000`.

## Docker

### Standalone (this service only)

```bash
cd ai_service
docker compose up --build
```

The service will be available at `http://localhost:8001`.

### Full-Stack (with Django app, PostgreSQL & Redis)

From the repository root:

```bash
docker compose up --build
```

This starts all services defined in the root `docker-compose.yml`:

| Service       | Internal Port | Host Port |
|---------------|---------------|-----------|
| `app` (Django)| 8000          | 8000      |
| `ai_service`  | 8000          | 8001      |
| `db` (Postgres)| 5432         | —         |
| `redis`       | 6379          | 6379      |

<details>
<summary><strong>Root <code>docker-compose.yml</code></strong></summary>

```yaml
services:
  app:
    build: ./library-management
    image: app
    command: bash -c "./wait-for-it.sh db:5432 -t 60 -- python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"
    volumes:
      - ./library-management:/app
    env_file:
      - ./library-management/.env
    depends_on:
      - db
      - redis
    ports:
      - "8000:8000"

  ai_service:
    build: ./ai_service
    image: ai_services
    volumes:
      - ./ai_service:/app
    ports:
      - "8001:8000"
    env_file:
      - ./ai_service/.env

  db:
    image: postgres:latest
    volumes:
      - postgres_data:/var/lib/postgresql
    env_file:
      - ./library-management/.env
    environment:
      - POSTGRES_DB=${DB_NAME:-library_management}
      - POSTGRES_USER=${DB_USER:-library_management}
      - POSTGRES_PASSWORD=${DB_PASSWORD:-library_management}

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

</details>
## Integration with the Django App

The Django application consumes this service through the LibraBot chat widget:

- **Frontend widget script:** `library-management/static/js/chatbot.js`
- **Widget markup:** `library-management/templates/components/chatbot.html`
- **CSP configuration:** Django's `CSP_CONNECT_SRC` includes `http://localhost:8001` for local development.

## Tech Stack

| Component  | Technology                       |
|------------|----------------------------------|
| Framework  | FastAPI 0.115                    |
| Server     | Uvicorn 0.34                     |
| AI Model   | OpenAI `gpt-4o-mini` (streaming)|
| Streaming  | SSE via `sse-starlette`          |
| Validation | Pydantic v2                      |
| Container  | Python 3.11-slim                 |

## Security Note

> [!WARNING]
> CORS is currently configured with `allow_origins=["*"]` in `main.py`. This **must** be restricted to the Django app's origin before deploying to production.
