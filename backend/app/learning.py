from __future__ import annotations

from collections import Counter
from typing import Any

from .ai import AIClient


class LearningEngine:
    def __init__(self, ai: AIClient) -> None:
        self.ai = ai

    def build_profile(
        self,
        interactions: list[dict[str, Any]],
        current_profile: dict[str, Any] | None,
        use_ai: bool = False,
    ) -> tuple[dict[str, Any], str]:
        current = current_profile or {}

        if use_ai and self.ai.enabled:
            ai_profile = self.ai.build_learning_profile(interactions, current)
            if ai_profile:
                return ai_profile, "ai"

        return self._heuristic_profile(interactions, current), "heuristic"

    def _heuristic_profile(
        self,
        interactions: list[dict[str, Any]],
        current_profile: dict[str, Any],
    ) -> dict[str, Any]:
        if not interactions:
            return {
                "persona_summary": "New profile. Add chats, tasks, and check-ins to learn your patterns.",
                "top_focus_areas": [],
                "friction_points": [],
                "preferred_response_style": [
                    "Simple language",
                    "Short action steps",
                    "One task at a time",
                ],
                "active_goals": current_profile.get("active_goals", []),
                "suggested_routines": ["Morning planning (5 minutes)", "Evening reset (5 minutes)"],
            }

        counts = Counter(item.get("event_type", "unknown") for item in interactions)
        text_blob = " ".join(item.get("content", "") for item in interactions).lower()

        focus_areas: list[str] = []
        if any(word in text_blob for word in ["school", "homework", "class", "study", "exam"]):
            focus_areas.append("School and learning")
        if any(word in text_blob for word in ["task", "project", "deadline", "schedule"]):
            focus_areas.append("Task and time management")
        if any(word in text_blob for word in ["stress", "overwhelmed", "anxious", "tired"]):
            focus_areas.append("Stress and energy regulation")
        if not focus_areas:
            focus_areas.append("General life organization")

        friction_points: list[str] = []
        if any(word in text_blob for word in ["forget", "forgot", "remember"]):
            friction_points.append("Memory and follow-through")
        if any(word in text_blob for word in ["distract", "focus", "adhd", "procrastin"]):
            friction_points.append("Sustained focus and distractions")
        if any(word in text_blob for word in ["overwhelmed", "stress", "pressure"]):
            friction_points.append("Overwhelm under workload")

        goals = list(current_profile.get("active_goals", []))
        if "School and learning" in focus_areas and "Stay on top of schoolwork" not in goals:
            goals.append("Stay on top of schoolwork")
        if "Task and time management" in focus_areas and "Finish top priorities daily" not in goals:
            goals.append("Finish top priorities daily")

        routines = [
            "Daily top-3 priorities",
            "25-minute focus sprint with 5-minute break",
            "2-minute task capture when new tasks appear",
        ]
        if counts.get("checkin", 0) > 0:
            routines.append("Morning and evening stress/focus check-in")

        return {
            "persona_summary": (
                "You do best with clear, simple explanations and short task chunks. "
                "The assistant should reduce overwhelm and keep you moving with one concrete next action."
            ),
            "top_focus_areas": focus_areas,
            "friction_points": friction_points,
            "preferred_response_style": [
                "Simple language",
                "Bullet-point action steps",
                "Gentle accountability",
            ],
            "active_goals": goals,
            "suggested_routines": routines,
            "signals": {
                "events_by_type": dict(counts),
                "total_events": len(interactions),
            },
        }
