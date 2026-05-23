# LibraBot — Chatbot Service

> A lightweight FastAPI microservice that powers the **LibraBot** chat widget in the [Library Management System](https://github.com/peterkahumu/Library-Management). It streams AI-generated responses to library-related questions via Server-Sent Events (SSE).

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green?style=flat-square)](https://github.com/peterkahumu/Library-Management/blob/main/LICENSE)

---

## Table of Contents

- [Why This Service?](#why-this-service)
- [How It Works](#how-it-works)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
  - [Standalone (This Service Only)](#standalone-this-service-only)
  - [Full-Stack (All Services)](#full-stack-all-services)
  - [Local Development (No Docker)](#local-development-no-docker)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Integration with the Django App](#integration-with-the-django-app)
- [Tech Stack](#tech-stack)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [Related Repositories](#related-repositories)
- [License](#license)

---

## Why This Service?

The Library Management System includes an embedded chat widget called **LibraBot** that helps students, librarians, and administrators get instant answers to library-related questions — borrowing policies, catalogue searches, fines, opening hours, and more.

This microservice is the backend that powers that widget. It accepts a conversation history, prepends a library-specific system prompt, and streams the response back token-by-token using Server-Sent Events for a responsive, real-time chat experience.

By running as a **separate service**, the chatbot can be independently deployed, scaled, and updated without touching the main Django application.

---

## How It Works

```
┌──────────────────┐       POST /chat/stream        ┌──────────────────┐
│  Django App      │ ──────────────────────────────► │  LibraBot        │
│  (Chat Widget)   │ ◄────────────── SSE stream ──── │  (This Service)  │
│  :8000           │                                 │  :8001           │
└──────────────────┘                                 └────────┬─────────┘
                                                              │
                                                     ┌────────▼─────────┐
                                                     │  OpenAI API      │
                                                     │  (gpt-4o-mini)   │
                                                     └──────────────────┘
```

1. The user types a question in the LibraBot widget.
2. The Django frontend sends the conversation history to `POST /chat/stream`.
3. This service prepends a library-focused system prompt and streams the response from OpenAI back as SSE events.
4. The widget renders each token as it arrives for a real-time typing effect.

---

## Architecture Overview

This service runs as an independent microservice within the broader Library Management platform. It communicates with the Django application over HTTP(S). Each service lives in its own repository and can be orchestrated together with a shared `docker-compose.yml` (see [Full-Stack setup](#full-stack-all-services)).

```
library-platform/                    # local project directory you create
├── library-management/              # Django app (consumes this service)
├── library-chatbot-service/         ← you are here
│   ├── main.py                      # FastAPI application entry point
│   ├── schemas.py                   # Pydantic request/response models
│   ├── Dockerfile                   # Container image definition
│   ├── docker-compose.yml           # Standalone compose (dev only)
│   ├── requirements.txt             # Python dependencies
│   └── .env_example                 # Environment variable template
├── recommendation_service/          # Book recommendation engine
└── docker-compose.yml               # Full-stack orchestration (you create this)
```

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Required for local development |
| Docker & Docker Compose | Latest stable | Required for containerized setup |
| OpenAI API Key | — | Required — the service calls the OpenAI chat completions API |

> **Note:** This service is stateless and does **not** require a database or Redis.

---

## Quick Start

### Standalone (This Service Only)

Use this when you want to run or test the chatbot independently:

1. Navigate to the service directory:

   ```bash
   cd library-chatbot-service
   ```

2. Create your environment file:

   ```bash
   cp .env_example .env
   # Edit .env — set OPENAI_API_KEY to your OpenAI key
   ```

3. Start the service:

   ```bash
   docker compose up --build
   ```

4. The service is available at `http://localhost:8001`.
5. Open `http://localhost:8001/docs` for the interactive Swagger UI.

### Full-Stack (All Services)

To run the **entire platform** — Django app, chatbot, recommendation engine, PostgreSQL, and Redis — clone all three repositories side-by-side and create a root `docker-compose.yml`.

1. **Create a project directory and clone all three repositories:**

   ```bash
   mkdir library-platform && cd library-platform

   git clone https://github.com/peterkahumu/Library-Management.git library-management
   git clone https://github.com/peterkahumu/library-chatbot-service.git library-chatbot-service
   git clone https://github.com/peterkahumu/library-recommendation-service.git recommendation_service
   ```

2. **Create the root `docker-compose.yml`** in `library-platform/`. Expand the block below and save the contents:

   <details>
   <summary><strong>Root <code>docker-compose.yml</code></strong> (click to expand)</summary>

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
       build: ./library-chatbot-service
       image: ai_services
       volumes:
         - ./library-chatbot-service:/app
       ports:
         - "8001:8000"
       env_file:
         - ./library-chatbot-service/.env

     recommendation_service:
       build: ./recommendation_service
       image: recommendation_service
       volumes:
         - ./recommendation_service:/app
       ports:
         - "8002:8000"
       env_file:
         - ./library-management/.env
       depends_on:
         - db

     db:
       image: pgvector/pgvector:pg16
       volumes:
         - postgres_data:/var/lib/postgresql/data
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

3. **Create the required `.env` files:**

   ```bash
   cp library-management/.env_example library-management/.env
   # Edit library-management/.env (set DB_HOST=db and REDIS_URL=redis://redis:6379)

   cp library-chatbot-service/.env_example library-chatbot-service/.env
   # Edit library-chatbot-service/.env — set OPENAI_API_KEY
   ```

4. **Start all services:**

   ```bash
   docker compose up --build
   ```

5. Open `http://localhost:8000` for the Django app.

This starts all services:

| Service | Description | Host Port |
|---------|-------------|-----------|
| `app` | Django web application | **8000** |
| `ai_service` | LibraBot chatbot (this service) | **8001** |
| `recommendation_service` | Book recommendations | **8002** |
| `db` | PostgreSQL with pgvector | — |
| `redis` | Redis cache | **6379** |

> For more details on Django-side configuration, see the [Library Management README](https://github.com/peterkahumu/Library-Management#full-stack-docker-compose).

### Local Development (No Docker)

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   # .venv\Scripts\activate    # Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:

   ```bash
   cp .env_example .env
   # Edit .env — set OPENAI_API_KEY
   ```

4. Start the server:

   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. The service is available at `http://localhost:8000`.
6. Visit `http://localhost:8000/docs` for the interactive API documentation.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | **Yes** | Your OpenAI API key for chat completions |
| `SYSTEM_PROMPT` | No | Override the default LibraBot system prompt (see `main.py` for the default) |

Create your `.env` from the template:

```bash
cp .env_example .env
```

---

## API Reference

### `GET /health`

Liveness probe used by orchestration tooling and health checks.

**Response** `200 OK`:

```json
{ "status": "healthy" }
```

---

### `POST /chat/stream`

Stream an AI-generated chat response via Server-Sent Events (SSE).

**Request body:**

```json
{
  "messages": [
    { "role": "user", "content": "How do I borrow a book?" }
  ]
}
```

The `messages` array is an ordered conversation history. Each message must include a `role` (`user` or `assistant`) and `content` string.

**SSE event stream:**

| Event | Payload | Description |
|-------|---------|-------------|
| `message` | `{ "content": "..." }` | Incremental response token |
| `error` | `{ "error": "..." }` | Error message if something went wrong |
| `done` | `{ "done": true }` | End-of-stream sentinel — close the connection |

**Example with `curl`:**

```bash
curl -N -X POST http://localhost:8001/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "What are the library opening hours?"}]}'
```

---

### Interactive API Docs

FastAPI auto-generates interactive API documentation:

- **Swagger UI:** `http://localhost:8001/docs`
- **ReDoc:** `http://localhost:8001/redoc`

---

## Integration with the Django App

The Django application consumes this service through the LibraBot chat widget:

| Integration Point | File | Description |
|-------------------|------|-------------|
| Frontend widget script | `library-management/static/js/chatbot.js` | JavaScript that opens an SSE connection to `/chat/stream` |
| Widget markup | `library-management/templates/components/chatbot.html` | Chat UI template embedded in the base layout |
| Service URL config | `AI_SERVICE_URL` in Django `.env` | Points the Django app at this service (default: `http://localhost:8001/`) |
| CSP configuration | Django `settings.py` | `CSP_CONNECT_SRC` includes `http://localhost:8001` for local development |

> The Django app degrades gracefully if this service is unavailable — the widget shows an error state instead of crashing the page.

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Framework | FastAPI 0.115 |
| Server | Uvicorn 0.34 |
| AI Model | OpenAI `gpt-4o-mini` (streaming) |
| Streaming | SSE via `sse-starlette` |
| Validation | Pydantic v2 |
| HTTP Client | `httpx` |
| Container | Python 3.11-slim |

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| `OPENAI_API_KEY is missing` warning | API key not set in `.env` | Create `.env` from `.env_example` and set your OpenAI key |
| SSE stream returns `error` event | OpenAI API failure or rate limit | Check the service logs; verify your API key is valid and has available quota |
| CORS errors in browser console | Origin not allowed | The service currently allows all origins (`*`). Check that the request URL matches the Django `AI_SERVICE_URL` |
| Widget not appearing in Django app | CSP blocking the connection | Verify `CSP_CONNECT_SRC` in Django settings includes the chatbot service URL |
| Connection refused on port 8001 | Service not running | Start the service with `docker compose up --build` or `uvicorn main:app` |

---

## Contributing

1. Fork this repository.
2. Create a feature branch: `git checkout -b feature/your-feature-name`.
3. Install dependencies and run the service locally (see [Local Development](#local-development-no-docker)).
4. Submit a pull request with a clear description of your changes.

---

## Related Repositories

| Repository | Description |
|-----------|-------------|
| [Library Management (Django App)](https://github.com/peterkahumu/Library-Management) | The main web application that consumes this chatbot service |
| [Recommendation Service](https://github.com/peterkahumu/library-recommendation-service) | Personality-based and similarity-based book recommendation engine |

---

## License

This project is licensed under the [MIT License](https://github.com/peterkahumu/Library-Management/blob/main/LICENSE).

Copyright © 2026 Peter Muhumuki.