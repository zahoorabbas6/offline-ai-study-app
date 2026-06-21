"""Safe optional Ollama integration for local AI mode."""

from __future__ import annotations

import json
import shutil
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from utils import Logger


@dataclass
class OllamaStatus:
    installed: bool = False
    running: bool = False
    active: bool = False
    model: Optional[str] = None
    message: str = "Ollama is not available."


class LocalAIManager:
    """Routes optional local AI requests through Ollama with silent fallback."""

    def __init__(self, base_url: str = "http://localhost:11434", model: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.preferred_model = model
        self.status = OllamaStatus()
        self.refresh_status()

    def refresh_status(self) -> OllamaStatus:
        installed = shutil.which("ollama") is not None
        running = False
        model = None
        message = "Ollama is not installed or not on PATH."

        try:
            data = self._get_json("/api/tags", timeout=1.5)
            models = data.get("models", []) if isinstance(data, dict) else []
            names = [item.get("name") for item in models if isinstance(item, dict) and item.get("name")]
            running = True
            if self.preferred_model and self.preferred_model in names:
                model = self.preferred_model
            elif names:
                model = names[0]
            message = "Ollama is running." if model else "Ollama is running, but no local model is installed."
        except Exception as exc:
            Logger.log_warning(f"Ollama detection fell back safely: {exc}")
            if installed:
                message = "Ollama is installed but not running at http://localhost:11434."

        self.status = OllamaStatus(
            installed=installed,
            running=running,
            active=installed and running and bool(model),
            model=model,
            message=message,
        )
        return self.status

    def is_active(self) -> bool:
        if self.status.active:
            return True
        return self.refresh_status().active

    def generate_text(self, prompt: str, system: str = "", timeout: int = 45) -> Optional[str]:
        if not self.is_active() or not self.status.model:
            return None

        payload = {
            "model": self.status.model,
            "prompt": prompt,
            "system": system,
            "stream": False,
            "options": {"temperature": 0.2},
        }
        try:
            response = self._post_json("/api/generate", payload, timeout=timeout)
            text = response.get("response", "") if isinstance(response, dict) else ""
            return text.strip() or None
        except Exception as exc:
            Logger.log_warning(f"Ollama generation failed safely: {exc}")
            self.status.active = False
            return None

    def generate_flashcards(self, text: str, count: int, memory_context: str = "") -> List[Dict[str, Any]]:
        prompt = f"""
Create exactly {count} study flashcards from the material.
Use the memory context only when it helps.
Return only valid JSON as an array of objects with:
question, answer, tags, difficulty, source.
Difficulty must be EASY, MEDIUM, or HARD.

Memory:
{memory_context}

Material:
{text[:9000]}
"""
        response = self.generate_text(prompt, "You create concise, accurate study flashcards.")
        cards = self._extract_json_array(response)
        cleaned = []
        for item in cards:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            answer = str(item.get("answer", "")).strip()
            if not question or not answer:
                continue
            tags = item.get("tags", [])
            if not isinstance(tags, list):
                tags = [str(tags)]
            difficulty = str(item.get("difficulty", "MEDIUM")).upper()
            if difficulty not in {"EASY", "MEDIUM", "HARD"}:
                difficulty = "MEDIUM"
            cleaned.append(
                {
                    "question": question,
                    "answer": answer,
                    "tags": [str(tag).strip() for tag in tags if str(tag).strip()],
                    "difficulty": difficulty,
                    "source": str(item.get("source", ""))[:500] or None,
                }
            )
        return cleaned[:count]

    def generate_exam_questions(self, text: str, count: int, memory_context: str = "") -> List[Dict[str, Any]]:
        prompt = f"""
Predict exactly {count} likely exam questions from the material.
Use the memory context to emphasize weak or repeated topics.
Return only valid JSON as an array of objects with:
question, type, probability, topic, reasoning, answer, options.
type must be one of MCQ, Short Answer, Long Answer, Definition, True/False.
probability must be HIGH, MEDIUM, or LOW.
options can be an empty array.

Memory:
{memory_context}

Material:
{text[:9000]}
"""
        response = self.generate_text(prompt, "You predict exam questions for students.")
        questions = self._extract_json_array(response)
        cleaned = []
        allowed_types = {"MCQ", "Short Answer", "Long Answer", "Definition", "True/False"}
        for item in questions:
            if not isinstance(item, dict):
                continue
            question = str(item.get("question", "")).strip()
            if not question:
                continue
            question_type = str(item.get("type", "Short Answer")).strip()
            if question_type not in allowed_types:
                question_type = "Short Answer"
            probability = str(item.get("probability", "MEDIUM")).upper()
            if probability not in {"HIGH", "MEDIUM", "LOW"}:
                probability = "MEDIUM"
            options = item.get("options") or []
            if not isinstance(options, list):
                options = []
            cleaned.append(
                {
                    "question": question,
                    "type": question_type,
                    "probability": probability,
                    "topic": str(item.get("topic", "General")).strip() or "General",
                    "reasoning": str(item.get("reasoning", "")).strip(),
                    "answer": str(item.get("answer", "See study material.")).strip(),
                    "options": [str(option).strip() for option in options if str(option).strip()],
                }
            )
        return cleaned[:count]

    def chat(self, message: str, current_text: str = "", memory_context: str = "") -> str:
        prompt = f"""
Use the available study context to answer the student.
You can explain concepts, create flashcards, create quizzes, or summarize uploaded content.
Be clear and useful. If context is missing, say what can be answered from the prompt.

Context:
{memory_context}

Current material:
{current_text[:6000]}

Student:
{message}
"""
        return self.generate_text(prompt, "You are a local offline AI study assistant.", timeout=60) or (
            "Local AI is unavailable right now. The core study tools still work with the offline fallback system."
        )

    def _get_json(self, path: str, timeout: float) -> Dict[str, Any]:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    def _post_json(self, path: str, payload: Dict[str, Any], timeout: int) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))

    @staticmethod
    def _extract_json_array(text: Optional[str]) -> List[Any]:
        if not text:
            return []

        candidates = [text]
        start = text.find("[")
        end = text.rfind("]")
        if start >= 0 and end > start:
            candidates.insert(0, text[start : end + 1])

        for candidate in candidates:
            try:
                parsed = json.loads(candidate)
                return parsed if isinstance(parsed, list) else []
            except Exception:
                continue
        return []


__all__ = ["LocalAIManager", "OllamaStatus"]
