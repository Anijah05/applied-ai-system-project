from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import List, Optional

from google import genai
from dotenv import load_dotenv

load_dotenv()

# ── Logging setup ────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler("pawpal.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("pawpal")


# ── GeminiAdvisor ─────────────────────────────────────────────────────────────
class GeminiAdvisor:
    """
    Wraps the Gemini API to provide AI-powered schedule explanations
    and answer follow-up pet care questions (agentic reasoning layer).
    """

    MODEL = "gemini-2.0-flash"

    def __init__(self) -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("GEMINI_API_KEY not set — AI features disabled.")
            self._enabled = False
            return
        self._client = genai.Client(api_key=api_key)
        self._enabled = True
        logger.info("GeminiAdvisor initialised (model: %s)", self.MODEL)

    @property
    def enabled(self) -> bool:
        return self._enabled

    def explain_schedule(
        self,
        owner_name: str,
        pet_names: List[str],
        available_minutes: int,
        scheduled_tasks: List[dict],
        excluded_tasks: List[dict],
        preferences: Optional[str] = None,
    ) -> str:
        """
        Ask Gemini to explain the generated schedule in plain English,
        reasoning about why each task was included or excluded.
        """
        if not self._enabled:
            return self._fallback_explanation(owner_name, scheduled_tasks, available_minutes)

        scheduled_lines = "\n".join(
            f"  - {t['title']} ({t['duration_minutes']} min, priority {t['priority']}, {t['category']})"
            for t in scheduled_tasks
        )
        excluded_lines = "\n".join(
            f"  - {t['title']} ({t['duration_minutes']} min, priority {t['priority']})"
            for t in excluded_tasks
        ) or "  None"

        prompt = f"""You are PawPal+, a friendly and knowledgeable pet care assistant.

Owner: {owner_name}
Pets: {', '.join(pet_names)}
Available time today: {available_minutes} minutes
Owner preferences: {preferences or 'None specified'}

Scheduled tasks:
{scheduled_lines}

Tasks that did NOT fit in the time budget:
{excluded_lines}

Write a warm, concise explanation (3-5 sentences) of today's schedule for {owner_name}.
Explain WHY tasks were prioritised in this order, mention the time budget trade-offs,
and offer one practical tip related to the highest-priority task.
Do not use bullet points — write in natural flowing prose."""

        try:
            logger.info("Requesting schedule explanation from Gemini.")
            response = self._client.models.generate_content(
                model=self.MODEL, contents=prompt
            )
            result = response.text.strip()
            logger.info("Gemini explanation received (%d chars).", len(result))
            return result
        except Exception as exc:
            logger.error("Gemini API error during explain_schedule: %s", exc)
            return self._fallback_explanation(owner_name, scheduled_tasks, available_minutes)

    def answer_question(
        self,
        question: str,
        context: str,
        chat_history: Optional[List[dict]] = None,
    ) -> str:
        """
        Answer a follow-up pet care question using the schedule as context.
        Maintains conversational history for multi-turn chat.
        """
        if not self._enabled:
            return "AI features are unavailable — please add your GEMINI_API_KEY to the .env file."

        history_text = ""
        if chat_history:
            history_text = "\n".join(
                f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
                for m in chat_history[-6:]  # last 3 turns
            )

        prompt = f"""You are PawPal+, a friendly and knowledgeable pet care assistant.

Current schedule context:
{context}

Previous conversation:
{history_text}

User question: {question}

Answer helpfully and concisely in 2-4 sentences. Stay focused on pet care advice.
If the question is unrelated to pets or the schedule, politely redirect."""

        try:
            logger.info("Answering follow-up question via Gemini.")
            response = self._client.models.generate_content(
                model=self.MODEL, contents=prompt
            )
            result = response.text.strip()
            logger.info("Gemini answer received (%d chars).", len(result))
            return result
        except Exception as exc:
            logger.error("Gemini API error during answer_question: %s", exc)
            return "Sorry, I couldn't reach the AI right now. Please try again in a moment."

    @staticmethod
    def _fallback_explanation(
        owner_name: str,
        scheduled_tasks: List[dict],
        available_minutes: int,
    ) -> str:
        total = sum(t["duration_minutes"] for t in scheduled_tasks)
        names = ", ".join(t["title"] for t in scheduled_tasks) if scheduled_tasks else "no tasks"
        return (
            f"Here's today's plan for {owner_name}: {names}. "
            f"These {len(scheduled_tasks)} task(s) use {total} of your {available_minutes} "
            f"available minutes, selected in priority order."
        )


# ── CareTask ──────────────────────────────────────────────────────────────────
@dataclass
class CareTask:
    title: str
    duration_minutes: int
    priority: int
    category: str
    is_recurring: bool = False
    is_completed: bool = False

    def update_priority(self, priority: int) -> None:
        if priority < 0:
            raise ValueError("Priority must be non-negative")
        self.priority = priority

    def update_duration(self, duration_minutes: int) -> None:
        if duration_minutes <= 0:
            raise ValueError("Duration must be positive")
        self.duration_minutes = duration_minutes

    def is_due(self) -> bool:
        return not self.is_completed or self.is_recurring

    def mark_complete(self) -> None:
        self.is_completed = True

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "category": self.category,
            "is_recurring": self.is_recurring,
            "is_completed": self.is_completed,
        }


# ── Pet ───────────────────────────────────────────────────────────────────────
@dataclass
class Pet:
    name: str
    species: str
    age: int
    tasks: List[CareTask] = field(default_factory=list)

    def add_task(self, task: CareTask) -> None:
        self.tasks.append(task)

    def edit_task(self, task: CareTask) -> None:
        for i, existing in enumerate(self.tasks):
            if existing.title == task.title:
                self.tasks[i] = task
                return
        raise ValueError(f"Task '{task.title}' not found for pet '{self.name}'")

    def get_tasks(self) -> List[CareTask]:
        return self.tasks


# ── Owner ─────────────────────────────────────────────────────────────────────
@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: Optional[str] = None
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        self.pets.append(pet)

    def update_preferences(self, preferences: Optional[str]) -> None:
        self.preferences = preferences

    def get_all_tasks(self) -> List[CareTask]:
        all_tasks = []
        for pet in self.pets:
            all_tasks.extend(pet.get_tasks())
        return all_tasks


# ── Scheduler ─────────────────────────────────────────────────────────────────
class Scheduler:
    def __init__(self, constraints: Optional[str] = None) -> None:
        self.constraints = constraints
        self.plan: List[CareTask] = []
        self.reasoning: Optional[str] = None
        self._advisor = GeminiAdvisor()

    def generate_plan(self, owner: Owner, tasks: List[CareTask]) -> List[CareTask]:
        logger.info(
            "Generating plan for %s (%d min available, %d tasks).",
            owner.name, owner.available_minutes, len(tasks),
        )
        filtered = self.filter_tasks_by_constraints(tasks)
        due = [t for t in filtered if t.is_due()]
        sorted_tasks = sorted(due, key=lambda t: t.priority, reverse=True)

        selected, total_time = [], 0
        for task in sorted_tasks:
            if total_time + task.duration_minutes <= owner.available_minutes:
                selected.append(task)
                total_time += task.duration_minutes

        excluded = [t for t in due if t not in selected]

        self.plan = selected
        self.reasoning = (
            f"Generated plan for {owner.name} with {owner.available_minutes} minutes available.\n"
            f"Selected {len(selected)} tasks totaling {total_time} minutes.\n"
            f"Tasks prioritized by urgency and importance."
        )
        if owner.preferences:
            self.reasoning += f"\nOwner preferences considered: {owner.preferences}"

        # AI explanation (replaces the static string when Gemini is available)
        pet_names = [p.name for p in owner.pets]
        self._ai_explanation = self._advisor.explain_schedule(
            owner_name=owner.name,
            pet_names=pet_names,
            available_minutes=owner.available_minutes,
            scheduled_tasks=[t.to_dict() for t in selected],
            excluded_tasks=[t.to_dict() for t in excluded],
            preferences=owner.preferences,
        )

        logger.info("Plan generated: %d tasks scheduled, %d excluded.", len(selected), len(excluded))
        return self.plan

    def get_ai_explanation(self) -> str:
        """Return the Gemini-generated explanation (call after generate_plan)."""
        return getattr(self, "_ai_explanation", self.reasoning or "No plan generated yet.")

    def answer_question(self, question: str, chat_history: Optional[List[dict]] = None) -> str:
        """Pass a follow-up question to GeminiAdvisor with schedule context."""
        context = self.get_ai_explanation()
        return self._advisor.answer_question(question, context, chat_history)

    def explain_plan(self) -> Optional[str]:
        """Legacy method — returns the static reasoning string."""
        return self.reasoning

    def filter_tasks_by_constraints(self, tasks: List[CareTask]) -> List[CareTask]:
        if not self.constraints:
            return tasks
        constraints_lower = self.constraints.lower()
        if "category:" in constraints_lower:
            category = constraints_lower.split("category:")[1].split()[0].strip()
            filtered = [t for t in tasks if t.category.lower() == category]
            logger.info("Constraint filter applied: category=%s → %d tasks.", category, len(filtered))
            return filtered
        return tasks