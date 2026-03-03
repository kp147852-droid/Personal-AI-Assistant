from __future__ import annotations

import json
from typing import Any

from openai import OpenAI

from .config import get_settings


class AIClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.model = settings.openai_model
        self.assistant_name = settings.assistant_name
        self._client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    @property
    def enabled(self) -> bool:
        return self._client is not None

    @staticmethod
    def _as_json(text: str) -> dict[str, Any]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _friendly_error(exc: Exception) -> str:
        msg = str(exc)
        lowered = msg.lower()
        if "insufficient_quota" in lowered or "exceeded your current quota" in lowered:
            return (
                "OpenAI quota exceeded for this API key. Update billing/limits in OpenAI platform "
                "or switch to another valid key."
            )
        if "invalid_api_key" in lowered or "incorrect api key" in lowered:
            return "OPENAI_API_KEY is invalid. Update backend/.env and restart the server."
        if "rate limit" in lowered:
            return "Rate limit reached. Wait a moment and retry."
        return f"AI request failed: {msg}"

    def _fallback_explain(self, content: str, reading_level: str) -> dict[str, Any]:
        short = " ".join(content.strip().split())
        if len(short) > 800:
            short = short[:800] + "..."
        return {
            "summary": f"Here is a simpler explanation ({reading_level.replace('_', ' ')}): {short}",
            "key_points": [
                "What this is mostly about",
                "The most important idea",
                "What to do next with this information",
            ],
            "steps_to_understand": [
                "Read the summary once without worrying about details.",
                "Pick one key point and restate it in your own words.",
                "Do one small action based on the content.",
            ],
        }

    def explain(self, content: str, reading_level: str) -> dict[str, Any]:
        if not self._client:
            return self._fallback_explain(content, reading_level)

        prompt = (
            "You are an ADHD-friendly tutor. Explain user content in plain language. "
            "Return JSON with keys: summary (string), key_points (array of 3-6 strings), "
            "steps_to_understand (array of 3-6 strings). "
            f"Target reading level: {reading_level}."
        )

        try:
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": content},
                ],
                text={"format": {"type": "json_object"}},
            )
            parsed = self._as_json(response.output_text)
            return parsed if parsed else self._fallback_explain(content, reading_level)
        except Exception as exc:
            return self._fallback_explain(self._friendly_error(exc), reading_level)

    def explain_image(self, image_b64: str, mime_type: str, reading_level: str) -> dict[str, Any]:
        if not self._client:
            return {
                "summary": "Image received. Add OPENAI_API_KEY to enable vision explanations.",
                "key_points": [
                    "Vision is currently disabled because no API key is configured.",
                    "You can still paste text for explanation right now.",
                    "After enabling AI, upload screenshots to get plain-English breakdowns.",
                ],
                "steps_to_understand": [
                    "Take a screenshot of what confuses you.",
                    "Upload it in the app.",
                    "Ask follow-up questions until it clicks.",
                ],
            }

        prompt = (
            "You are an ADHD-friendly tutor. Explain this image in plain language. "
            "Return JSON with keys: summary, key_points (3-6), steps_to_understand (3-6). "
            f"Target reading level: {reading_level}."
        )
        try:
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": prompt},
                            {
                                "type": "input_image",
                                "image_url": f"data:{mime_type};base64,{image_b64}",
                            },
                        ],
                    }
                ],
                text={"format": {"type": "json_object"}},
            )
            parsed = self._as_json(response.output_text)
            if parsed:
                return parsed
            return self._fallback_explain("Unable to parse image explanation.", reading_level)
        except Exception as exc:
            return self._fallback_explain(self._friendly_error(exc), reading_level)

    def chat(self, message: str, memory_snippets: list[str]) -> str:
        memory_context = "\n".join(f"- {item}" for item in memory_snippets[-8:])
        system = (
            f"You are {self.assistant_name}, a practical life assistant for someone with ADHD. "
            "Be supportive but direct. Keep answers short, clear, and actionable. "
            "When useful, break work into tiny next steps."
        )

        if not self._client:
            return (
                "AI mode is currently offline. Add OPENAI_API_KEY in backend/.env, restart the server, "
                "then I can answer your actual question."
            )

        try:
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": system},
                    {
                        "role": "user",
                        "content": f"Memory:\n{memory_context}\n\nUser message:\n{message}",
                    },
                ],
            )
            return response.output_text
        except Exception as exc:
            return self._friendly_error(exc)

    def coach(self, stress_level: int, focus_level: int, notes: str | None) -> dict[str, str]:
        if not self._client:
            action = "Pick one task, set a 10-minute timer, and remove one distraction before starting."
            return {
                "coaching": "Small wins first. You do not need a perfect day, just one completed step.",
                "next_action": action,
            }

        prompt = (
            "Give ADHD-friendly micro-coaching. Return JSON with keys: coaching and next_action. "
            "Keep next_action under 20 words and specific."
        )
        user = f"Stress: {stress_level}/10, Focus: {focus_level}/10, Notes: {notes or 'None'}"

        try:
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": user},
                ],
                text={"format": {"type": "json_object"}},
            )
            parsed = self._as_json(response.output_text)
            if "coaching" in parsed and "next_action" in parsed:
                return {"coaching": str(parsed["coaching"]), "next_action": str(parsed["next_action"])}
        except Exception as exc:
            return {
                "coaching": self._friendly_error(exc),
                "next_action": "Retry when API access is available.",
            }
        return {
            "coaching": "Take one small step now. Momentum beats perfection.",
            "next_action": "Choose one task and do 5 minutes right now.",
        }
