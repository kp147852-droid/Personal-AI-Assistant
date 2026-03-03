from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "assistant.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                details TEXT,
                due_date TEXT,
                priority TEXT NOT NULL DEFAULT 'medium',
                status TEXT NOT NULL DEFAULT 'todo',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS checkins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stress_level INTEGER NOT NULL,
                focus_level INTEGER NOT NULL,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS learning_profile (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                profile_json TEXT NOT NULL,
                source TEXT NOT NULL,
                events_analyzed INTEGER NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


def log_interaction(event_type: str, content: str, metadata: dict[str, Any] | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO interactions(event_type, content, metadata) VALUES(?, ?, ?)",
            (event_type, content, json.dumps(metadata or {})),
        )


def get_recent_interactions(limit: int = 150) -> list[dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, event_type, content, metadata, created_at FROM interactions ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    parsed: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        try:
            item["metadata"] = json.loads(item.get("metadata") or "{}")
        except json.JSONDecodeError:
            item["metadata"] = {}
        parsed.append(item)
    return list(reversed(parsed))


def get_learning_profile() -> dict[str, Any] | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT profile_json, source, events_analyzed, updated_at FROM learning_profile WHERE id = 1"
        ).fetchone()
    if not row:
        return None
    payload = dict(row)
    try:
        payload["profile"] = json.loads(payload.pop("profile_json"))
    except json.JSONDecodeError:
        payload["profile"] = {}
    return payload


def save_learning_profile(profile: dict[str, Any], source: str, events_analyzed: int) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO learning_profile(id, profile_json, source, events_analyzed)
            VALUES(1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              profile_json = excluded.profile_json,
              source = excluded.source,
              events_analyzed = excluded.events_analyzed,
              updated_at = CURRENT_TIMESTAMP
            """,
            (json.dumps(profile), source, events_analyzed),
        )
