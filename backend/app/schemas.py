from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)


class ChatResponse(BaseModel):
    reply: str


class ExplainRequest(BaseModel):
    content: str = Field(min_length=1, max_length=20000)
    reading_level: str = Field(default="middle_school")


class ExplainResponse(BaseModel):
    summary: str
    key_points: list[str]
    steps_to_understand: list[str]


class MemoryCreate(BaseModel):
    category: str
    content: str


class TaskCreate(BaseModel):
    title: str
    details: str | None = None
    due_date: str | None = None
    priority: str = "medium"


class TaskUpdate(BaseModel):
    status: str


class CheckinCreate(BaseModel):
    stress_level: int = Field(ge=1, le=10)
    focus_level: int = Field(ge=1, le=10)
    notes: str | None = None


class CoachingResponse(BaseModel):
    coaching: str
    next_action: str
