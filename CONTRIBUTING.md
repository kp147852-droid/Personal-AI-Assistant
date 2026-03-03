# Contributing

Thanks for contributing to Personal AI Assistant.

## Dev setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Run API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Pull request expectations

- Keep changes scoped and explain why in the PR description.
- Add or update tests when behavior changes.
- Do not commit secrets (`.env`, API keys, tokens).
- Preserve privacy defaults for user data.

## Code style

- Python: type hints preferred, concise functions, no dead code.
- Frontend: plain JavaScript and semantic HTML/CSS.
