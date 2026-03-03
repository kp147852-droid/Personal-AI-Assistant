from __future__ import annotations

import base64
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .ai import AIClient
from .config import get_settings
from .db import get_conn, init_db
from .schemas import (
    ChatRequest,
    ChatResponse,
    CheckinCreate,
    CoachingResponse,
    ExplainRequest,
    ExplainResponse,
    MemoryCreate,
    TaskCreate,
    TaskUpdate,
)

app = FastAPI(title="Personal Assistant API")
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(settings.trusted_hosts))

ai = AIClient()
LOCAL_CLIENTS = {"127.0.0.1", "::1", "localhost"}


@app.on_event("startup")
def startup() -> None:
    if not settings.single_user_mode:
        raise RuntimeError("SINGLE_USER_MODE must stay enabled for this build.")
    init_db()


@app.middleware("http")
async def local_only_clients(request: Request, call_next):
    # Enforce strict single-device access even if bind settings are changed.
    host = request.client.host if request.client else ""
    if host not in LOCAL_CLIENTS:
        return JSONResponse(status_code=403, content={"detail": "Local-only access enforced."})
    return await call_next(request)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "ai_enabled": ai.enabled, "single_user_mode": settings.single_user_mode}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT content FROM memory ORDER BY id DESC LIMIT 8"
        ).fetchall()
    memory_items = [r["content"] for r in rows]
    reply = ai.chat(payload.message, memory_items)
    return ChatResponse(reply=reply)


@app.post("/api/explain", response_model=ExplainResponse)
def explain(payload: ExplainRequest) -> ExplainResponse:
    data = ai.explain(payload.content, payload.reading_level)
    return ExplainResponse(**data)


@app.post("/api/explain-image", response_model=ExplainResponse)
async def explain_image(file: UploadFile = File(...)) -> ExplainResponse:
    allowed = {"image/png", "image/jpeg", "image/webp"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only PNG/JPEG/WEBP images are supported.")

    image_bytes = await file.read()
    if len(image_bytes) > 8_000_000:
        raise HTTPException(status_code=400, detail="Image too large. Max 8MB.")

    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data = ai.explain_image(b64, file.content_type, "middle_school")
    return ExplainResponse(**data)


@app.post("/api/memory")
def add_memory(payload: MemoryCreate) -> dict[str, str]:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO memory(category, content) VALUES(?, ?)",
            (payload.category, payload.content),
        )
    return {"status": "saved"}


@app.get("/api/memory")
def list_memory() -> list[dict[str, str | int]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, category, content, created_at FROM memory ORDER BY id DESC LIMIT 50"
        ).fetchall()
    return [dict(r) for r in rows]


@app.post("/api/tasks")
def create_task(payload: TaskCreate) -> dict[str, str | int]:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO tasks(title, details, due_date, priority) VALUES(?, ?, ?, ?)",
            (payload.title, payload.details, payload.due_date, payload.priority),
        )
        task_id = cur.lastrowid
    return {"status": "created", "task_id": task_id}


@app.get("/api/tasks")
def list_tasks() -> list[dict[str, str | int]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, title, details, due_date, priority, status, created_at FROM tasks ORDER BY id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


@app.patch("/api/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate) -> dict[str, str]:
    with get_conn() as conn:
        cur = conn.execute(
            "UPDATE tasks SET status = ? WHERE id = ?",
            (payload.status, task_id),
        )
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "updated"}


@app.post("/api/checkin", response_model=CoachingResponse)
def checkin(payload: CheckinCreate) -> CoachingResponse:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO checkins(stress_level, focus_level, notes) VALUES(?, ?, ?)",
            (payload.stress_level, payload.focus_level, payload.notes),
        )

    data = ai.coach(payload.stress_level, payload.focus_level, payload.notes)
    return CoachingResponse(**data)


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/app/")

@app.get("/app")
def app_root() -> RedirectResponse:
    return RedirectResponse(url="/app/")

@app.get("/alpha")
def alpha_root() -> RedirectResponse:
    return RedirectResponse(url="/app/")

@app.get("/Alpha")
def alpha_root_caps() -> RedirectResponse:
    return RedirectResponse(url="/app/")


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="app")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
