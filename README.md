# Alpha (Local Personal AI Assistant)

Alpha is designed as a **strict single-user local app**. Each person who installs it runs their own instance and local database.

## Privacy/Isolation Model

- Alpha stores memory/tasks/check-ins in local SQLite on that machine.
- Backend binds to `127.0.0.1` by default (not publicly reachable).
- Requests from non-local client IPs are rejected by middleware.
- Trusted host and CORS defaults are limited to localhost origins.
- Relay/peer communication code is removed from this project.
- `SINGLE_USER_MODE=true` is enforced at backend startup.

## 1) Backend setup (Mac)

```bash
cd "/Users/kyleparker/Documents/New project 2/data/AI assistant/backend"
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set API key in `.env`:

```bash
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4.1-mini
ASSISTANT_NAME=Alpha
```

Run:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Open:
- `http://localhost:8000/app`

## 2) Run continuously on Mac (optional)

```bash
cd "/Users/kyleparker/Documents/New project 2/data/AI assistant"
./scripts/install_launchd.sh
```

Useful commands:

```bash
launchctl list | grep focusmate
launchctl unload ~/Library/LaunchAgents/com.focusmate.backend.plist
launchctl load ~/Library/LaunchAgents/com.focusmate.backend.plist
```

Logs:
- `/Users/kyleparker/Documents/New project 2/data/AI assistant/backend/data/launchd.out.log`
- `/Users/kyleparker/Documents/New project 2/data/AI assistant/backend/data/launchd.err.log`

## 3) iPhone usage (strict isolation)

Run a separate Alpha installation per device/user:
- Mac Alpha: local DB on Mac.
- iPhone Alpha: its own local app/runtime and storage.

This repository intentionally does not include user-to-user or Alpha-to-Alpha connection features.
