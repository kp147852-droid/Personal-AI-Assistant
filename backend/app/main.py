from __future__ import annotations

import base64
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .ai import AIClient
from .db import (
    get_conn,
    get_learning_profile,
    get_recent_interactions,
    init_db,
    log_interaction,
    save_learning_profile,
)
from .learning import LearningEngine
from .schemas import (
    ChatRequest,
    ChatResponse,
    CheckinCreate,
    CoachingResponse,
    ExplainRequest,
    ExplainResponse,
    LearningProfileResponse,
    LearningRefreshRequest,
    MemoryCreate,
    TaskCreate,
    TaskUpdate,
)

app = FastAPI(title="Personal Assistant API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai = AIClient()
learning = LearningEngine(ai)


@app.on_event("startup")
def startup() -> None:
    init_db()


def refresh_learning_profile(use_ai: bool = False) -> LearningProfileResponse:
    interactions = get_recent_interactions(limit=150)
    existing = get_learning_profile()
    current = existing["profile"] if existing else {}
    profile, source = learning.build_profile(interactions, current, use_ai=use_ai)
    save_learning_profile(profile, source=source, events_analyzed=len(interactions))

    saved = get_learning_profile()
    if not saved:
        return LearningProfileResponse(profile=profile, source=source, events_analyzed=len(interactions))
    return LearningProfileResponse(
        profile=saved["profile"],
        source=str(saved["source"]),
        events_analyzed=int(saved["events_analyzed"]),
        updated_at=str(saved["updated_at"]),
    )


def log_and_learn(event_type: str, content: str, metadata: dict | None = None) -> None:
    log_interaction(event_type=event_type, content=content[:2000], metadata=metadata)
    refresh_learning_profile(use_ai=False)


@app.get("/health")
def health() -> dict[str, str | bool]:
    return {"status": "ok", "ai_enabled": ai.enabled}


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT content FROM memory ORDER BY id DESC LIMIT 8"
        ).fetchall()
    memory_items = [r["content"] for r in rows]
    profile = get_learning_profile()
    profile_data = profile["profile"] if profile else None

    reply = ai.chat(payload.message, memory_items, profile=profile_data)
    log_and_learn("chat", payload.message)
    return ChatResponse(reply=reply)


@app.post("/api/explain", response_model=ExplainResponse)
def explain(payload: ExplainRequest) -> ExplainResponse:
    data = ai.explain(payload.content, payload.reading_level)
    log_and_learn("explain_text", payload.content, {"reading_level": payload.reading_level})
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
    log_and_learn("explain_image", f"uploaded:{file.filename or 'image'}", {"mime_type": file.content_type})
    return ExplainResponse(**data)


@app.post("/api/memory")
def add_memory(payload: MemoryCreate) -> dict[str, str]:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO memory(category, content) VALUES(?, ?)",
            (payload.category, payload.content),
        )
    log_and_learn("memory_add", payload.content, {"category": payload.category})
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
    log_and_learn("task_create", payload.title, {"priority": payload.priority, "due_date": payload.due_date})
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
    log_and_learn("task_update", f"task:{task_id}", {"status": payload.status})
    return {"status": "updated"}


@app.post("/api/checkin", response_model=CoachingResponse)
def checkin(payload: CheckinCreate) -> CoachingResponse:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO checkins(stress_level, focus_level, notes) VALUES(?, ?, ?)",
            (payload.stress_level, payload.focus_level, payload.notes),
        )

    data = ai.coach(payload.stress_level, payload.focus_level, payload.notes)
    log_and_learn(
        "checkin",
        payload.notes or "checkin",
        {"stress_level": payload.stress_level, "focus_level": payload.focus_level},
    )
    return CoachingResponse(**data)


@app.get("/api/learning/profile", response_model=LearningProfileResponse)
def learning_profile() -> LearningProfileResponse:
    saved = get_learning_profile()
    if saved:
        return LearningProfileResponse(
            profile=saved["profile"],
            source=str(saved["source"]),
            events_analyzed=int(saved["events_analyzed"]),
            updated_at=str(saved["updated_at"]),
        )
    return refresh_learning_profile(use_ai=False)


@app.post("/api/learning/refresh", response_model=LearningProfileResponse)
def learning_refresh(payload: LearningRefreshRequest) -> LearningProfileResponse:
    return refresh_learning_profile(use_ai=payload.use_ai)


@app.get("/")
def root() -> RedirectResponse:
    return RedirectResponse(url="/app")


FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/app", StaticFiles(directory=FRONTEND_DIR, html=True), name="app")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
