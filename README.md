# Personal AI Assistant (MacBook + iPhone)

Your own AI assistant software that:
- Explains documents, screenshots, and tasks in simpler language.
- Learns continuously from your interactions and builds a personalized profile.
- Helps with ADHD-friendly planning, reminders, and stress/focus coaching.
- Runs on your MacBook and is available on iPhone.

## Core architecture

- Backend: `FastAPI` + `SQLite`
- AI: OpenAI Responses API (optional but recommended)
- Frontend: installable web app (PWA)
- Continuous mode: macOS `launchd`

## Continuous learning model

The app updates a `learning_profile` from your real usage:
- `chat`, `explain_text`, `explain_image`
- `task_create`, `task_update`
- `memory_add`, `checkin`

Profile fields include:
- persona summary
- focus areas
- friction points
- preferred response style
- active goals
- suggested routines

Endpoints:
- `GET /api/learning/profile`
- `POST /api/learning/refresh` with `{ "use_ai": true }` for AI-enhanced profile synthesis

## 1) Local setup

```bash
cd "/Users/kyleparker/Documents/New project 2/data/Personal AI assistant/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set `.env`:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
ASSISTANT_NAME=FocusMate
```

Run backend + app UI:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open on MacBook:
- `http://localhost:8000/app`

## 2) iPhone access

On same Wi-Fi, find Mac IP:

```bash
ipconfig getifaddr en0
```

Open on iPhone Safari:
- `http://<your-mac-ip>:8000/app`

Install on iPhone Home Screen:
1. Safari Share button
2. `Add to Home Screen`

## 3) Run continuously on MacBook

```bash
cd "/Users/kyleparker/Documents/New project 2/data/Personal AI assistant"
./scripts/install_launchd.sh
```

Check service:

```bash
launchctl list | grep focusmate
```

## 4) Publish to GitHub

Create an empty GitHub repo named `personal-ai-assistant`, then run:

```bash
cd "/Users/kyleparker/Documents/New project 2/data/Personal AI assistant"
git add .
git commit -m "Initial commit: Personal AI Assistant with continuous learning"
git remote add origin git@github.com:<your-username>/personal-ai-assistant.git
git push -u origin main
```

## 5) Privacy notes

- Your local data is stored in `backend/data/assistant.db`.
- `.env` and database files are git-ignored.
- If you open-source the project, do not publish personal database files or secrets.
