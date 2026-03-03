# Architecture

## High-Level Flow

1. User opens `http://localhost:8000/app/`.
2. Frontend sends requests to backend API endpoints (`/api/chat`, `/api/explain`, `/api/explain-image`, `/api/checkin`).
3. Backend reads/writes local SQLite for memory/task/check-in context.
4. Backend calls AI provider when API key is configured.
5. Response is returned to frontend in chat-style UX.

## Components

- `backend/app/main.py`: FastAPI routes, local-only enforcement, static app mount.
- `backend/app/ai.py`: AI client integration, prompts, fallback/error normalization.
- `backend/app/db.py`: SQLite connection and schema initialization.
- `frontend/index.html`: single-page chat UI.
- `frontend/app.js`: chat/voice/image interaction logic.
- `frontend/styles.css`: red/black chat-style theme.

## Data Model

- `memory`: user notes/context
- `tasks`: user action tracking
- `checkins`: stress/focus coaching context

## Deployment Model

- Local machine runtime via `uvicorn`.
- Optional always-on operation using macOS `launchd`.

## Design Decisions

- Local-first data storage for privacy.
- Single-user enforced mode to prevent accidental cross-user communication.
- Minimal dependencies to keep setup straightforward for evaluators/recruiters.
