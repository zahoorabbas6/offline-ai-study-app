"""Persistent, failure-safe learning memory for the study app."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from utils import Logger, TextAnalyzer


class StudyMemory:
    """Small JSON-backed memory store that never raises into the app."""

    DEFAULT_DATA = {
        "version": 1,
        "documents": [],
        "flashcards": [],
        "quiz_results": [],
        "exam_questions": [],
        "chat_history": [],
    }

    def __init__(self, data_dir: str = "study_data", filename: str = "study_memory.json"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.path = self.data_dir / filename
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return dict(self.DEFAULT_DATA)

        try:
            with open(self.path, "r", encoding="utf-8") as file:
                loaded = json.load(file)
            if not isinstance(loaded, dict):
                raise ValueError("Memory file must contain a JSON object")

            merged = dict(self.DEFAULT_DATA)
            for key, value in loaded.items():
                if key in merged:
                    merged[key] = value if isinstance(value, type(merged[key])) else merged[key]
            return merged
        except Exception as exc:
            Logger.log_warning(f"Memory file could not be loaded and will be reset safely: {exc}")
            backup = self.path.with_suffix(".corrupt.json")
            try:
                self.path.replace(backup)
            except Exception:
                pass
            return dict(self.DEFAULT_DATA)

    def save(self) -> bool:
        try:
            temp_path = self.path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as file:
                json.dump(self.data, file, indent=2, ensure_ascii=False)
            temp_path.replace(self.path)
            return True
        except Exception as exc:
            Logger.log_warning(f"Memory save skipped safely: {exc}")
            return False

    def add_document(self, text: str, source: str = "input", summary: str = "") -> None:
        if not text:
            return

        try:
            record = {
                "timestamp": self._timestamp(),
                "source": source,
                "hash": TextAnalyzer.calculate_text_hash(text),
                "summary": summary or text[:500],
                "metadata": TextAnalyzer.get_stats(text),
            }
            if not any(item.get("hash") == record["hash"] for item in self.data["documents"]):
                self.data["documents"].append(record)
                self._trim("documents", 30)
                self.save()
        except Exception as exc:
            Logger.log_warning(f"Document memory update skipped safely: {exc}")

    def add_flashcards(self, cards: List[Dict[str, Any]]) -> None:
        self._append_record("flashcards", {"cards": cards}, limit=40)

    def add_exam_questions(self, questions: List[Dict[str, Any]]) -> None:
        self._append_record("exam_questions", {"questions": questions}, limit=40)

    def add_quiz_result(self, result: Dict[str, Any]) -> None:
        self._append_record("quiz_results", {"result": result}, limit=50)

    def add_chat_turn(self, user_message: str, ai_response: str) -> None:
        self._append_record(
            "chat_history",
            {"user": user_message, "assistant": ai_response},
            limit=80,
        )

    def build_context(self, current_text: str = "", max_chars: int = 2500) -> str:
        """Return compact context for local AI prompts."""
        try:
            parts = []
            if current_text:
                parts.append("Current study material:\n" + current_text[:1200])

            documents = self.data.get("documents", [])[-3:]
            if documents:
                parts.append(
                    "Recent document summaries:\n"
                    + "\n".join(f"- {item.get('summary', '')[:240]}" for item in documents)
                )

            quiz_results = self.data.get("quiz_results", [])[-3:]
            if quiz_results:
                summaries = []
                for item in quiz_results:
                    result = item.get("result", {})
                    summaries.append(
                        f"- {result.get('quiz_name', 'Quiz')}: "
                        f"{result.get('score_percentage', 0):.1f}%"
                    )
                parts.append("Recent quiz performance:\n" + "\n".join(summaries))

            chats = self.data.get("chat_history", [])[-4:]
            if chats:
                parts.append(
                    "Recent chat:\n"
                    + "\n".join(
                        f"User: {item.get('user', '')[:160]}\nAI: {item.get('assistant', '')[:220]}"
                        for item in chats
                    )
                )

            return "\n\n".join(parts)[:max_chars]
        except Exception as exc:
            Logger.log_warning(f"Memory context skipped safely: {exc}")
            return current_text[:max_chars] if current_text else ""

    def _append_record(self, key: str, payload: Dict[str, Any], limit: int) -> None:
        try:
            if not payload:
                return
            record = {"timestamp": self._timestamp(), **payload}
            self.data.setdefault(key, []).append(record)
            self._trim(key, limit)
            self.save()
        except Exception as exc:
            Logger.log_warning(f"Memory update for {key} skipped safely: {exc}")

    def _trim(self, key: str, limit: int) -> None:
        values = self.data.get(key, [])
        if isinstance(values, list) and len(values) > limit:
            self.data[key] = values[-limit:]

    @staticmethod
    def _timestamp() -> str:
        return datetime.now().isoformat(timespec="seconds")


__all__ = ["StudyMemory"]
