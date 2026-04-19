# PawPal+ — Applied AI System

An intelligent pet care planning assistant powered by a priority-based scheduling algorithm and Gemini AI. PawPal+ helps busy pet owners optimize their daily care routines across multiple pets, then explains the schedule in plain language and answers follow-up questions.

---

## Original Project

This project is an evolution of **PawPal+ (Module 2)** from the AI110 course. The original project established the core OOP architecture — `CareTask`, `Pet`, `Owner`, and `Scheduler` classes — and a priority-based greedy scheduling algorithm with a Streamlit UI. It demonstrated modular system design and algorithmic task planning but had no AI integration; the schedule explanation was a static template string.

---

## What's New in This Version

- **Gemini AI integration** via a new `GeminiAdvisor` class that generates natural language schedule explanations and powers a multi-turn follow-up chat
- **Agentic reasoning**: Gemini receives structured schedule context and reasons about priority trade-offs, time budget decisions, and pet care tips
- **Graceful fallback**: the system works fully without an API key, falling back to the static explanation
- **Logging**: all AI calls, errors, and plan generation events are recorded to `pawpal.log`
- **Error guardrails**: every API call is wrapped in try/except with informative fallback responses
- **Expanded test suite**: 25 tests covering all core logic and the new AI layer using mocks

---

## System Architecture

PawPal+ is organized into four core classes and one AI advisor class:

- **`CareTask`** — represents a single pet care activity with title, duration, priority, category, and completion state
- **`Pet`** — owns a list of `CareTask` objects; supports add, edit, and retrieval
- **`Owner`** — owns a list of `Pet` objects and aggregates tasks across all pets; holds time budget and preferences
- **`Scheduler`** — the planning engine; filters, sorts, and greedily selects tasks that fit the time budget; calls `GeminiAdvisor` to explain the result
- **`GeminiAdvisor`** — the AI layer; wraps the Gemini API to generate natural language explanations and answer follow-up questions with schedule context

Data flows as follows: the user provides owner info, pets, and tasks through the Streamlit UI → `Scheduler.generate_plan()` filters and ranks tasks → `GeminiAdvisor.explain_schedule()` receives the structured plan and returns a plain-English explanation → the user can ask follow-up questions via `GeminiAdvisor.answer_question()` which maintains conversational history.

See `/assets/architecture_diagram.png` for the full UML class diagram.

---

## Setup Instructions

**1. Clone the repo:**
```bash
git clone https://github.com/Anijah05/applied-ai-system-project.git
cd applied-ai-system-project
```

**2. Create and activate a virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**3. Install dependencies:**
```bash
pip install -r requirements.txt
```

**4. Add your Gemini API key:**

Create a `.env` file in the project root:
```
GEMINI_API_KEY=your_key_here
```
Get a free key at [aistudio.google.com](https://aistudio.google.com). The app runs without a key but AI features will use a fallback explanation.

**5. Run the app:**
```bash
streamlit run app.py
```

**6. Run the tests:**
```bash
pytest test_pawpal.py -v
```

---

## Sample Interactions

**Example 1 — Basic schedule generation:**

Input: Owner "Jordan", 120 minutes available, one dog "Mochi" with tasks: Morning walk (30 min, priority 10), Feed breakfast (10 min, priority 9), Brush teeth (5 min, priority 5), Bath (60 min, priority 3).

Gemini explanation output:
> "Jordan, here's your optimized plan for Mochi today! I've prioritized the morning walk first since it's your highest-urgency task and a great way to start the day — consistency with exercise routines is really important for dogs. Breakfast feeding follows right after, and I've squeezed in a quick teeth brushing session too. The bath didn't make the cut today since it would push you over your 120-minute budget, but consider scheduling it for a day when you have a bit more time."

**Example 2 — Follow-up chat question:**

User: "Why wasn't the bath scheduled?"

Gemini response:
> "The bath was excluded because adding its 60 minutes would have brought the total to 105 minutes and left no room for the remaining tasks. Since the bath had the lowest priority (3), the scheduler kept the higher-priority tasks and dropped it. You could schedule it on its own on a lighter day!"

**Example 3 — Category constraint filtering:**

Input: Constraints set to `category:exercise`, owner has feeding and exercise tasks.

Result: Only exercise tasks are scheduled. Gemini explanation notes the constraint was applied and explains the filtered selection.

---

## Design Decisions

**Why a greedy scheduler?** A greedy approach (sort by priority, select until time runs out) is simple, explainable, and performs well for this use case. An optimal knapsack solution would be more accurate but harder to explain to a non-technical user, and explainability matters more here than mathematical optimality.

**Why `GeminiAdvisor` as a separate class?** Keeping AI logic isolated from the scheduling logic means the scheduler can be tested without any API calls, and the AI layer can be swapped out or extended independently. It also makes the fallback behavior clean — if Gemini is unavailable, nothing else breaks.

**Why graceful fallback instead of failing hard?** Pet owners shouldn't lose their schedule because of an API timeout. The fallback static explanation still gives the user a usable result, and the error is logged for debugging.

**Why `google-genai` instead of `google-generativeai`?** The older package was deprecated by Google in 2025. Switching to the current SDK avoids future compatibility issues.

**Trade-offs:** The greedy scheduler can miss combinations where a lower-priority task fits perfectly and allows more total tasks. This is a known limitation — a future version could use dynamic programming for better packing. The Gemini prompts are also stateless per call; a production version would benefit from persistent conversation sessions.

---

## Testing Summary

25 tests, 25 passed, 0 failures.

Tests cover: task completion and recurring logic, task addition and editing, priority-based sorting, time budget enforcement, multi-pet aggregation, input validation, category constraint filtering, completed task exclusion, `to_dict()` serialization, and the full AI layer.

For the AI layer specifically, tests use `unittest.mock.patch.dict` to remove the API key from the environment, forcing `GeminiAdvisor` into disabled mode. This means the test suite runs in under 4 seconds with no real API calls, while still verifying that fallback behavior, disabled messages, and explanation content are all correct.

One area of note: the scheduler does not currently test for cases where a lower-priority short task could fill remaining time after a high-priority long task — this is a known gap in the greedy approach and a candidate for a future test.

---

## Reflection and Ethics

**Limitations and biases:** The scheduling algorithm is purely priority-based and does not account for task dependencies (e.g., feeding before medication), time-of-day preferences, or pet-specific needs by species. The Gemini explanations are only as good as the prompt — if task data is sparse, the explanation may be vague. The system also has no memory between sessions, so recurring routines must be re-entered each time.

**Potential misuse:** A user could over-rely on the AI explanation and skip tasks the scheduler excluded without understanding why. To mitigate this, excluded tasks are always shown with their reason (time budget), and the algorithm details are visible in an expander. The AI is framed as an explainer, not a medical advisor — it does not give veterinary advice.

**Surprises during testing:** The mock-based tests revealed that `GeminiAdvisor` needed a cleaner separation between initialization and API calls — early versions would throw an exception at import time if the key was missing rather than at call time. Moving the key check into `__init__` and setting `_enabled = False` fixed this and made the fallback behavior much more predictable.

**AI collaboration:** Gemini was helpful when generating the prompt structure for `explain_schedule()` — it suggested including excluded tasks in the prompt so the AI could explain what didn't make the cut, which made the explanations much more useful. One instance where AI suggestions were flawed: an early suggestion used the deprecated `google.generativeai` package and the `GenerativeModel` class, which produced a `FutureWarning` and would have broken in a future SDK update. Switching to the current `google-genai` SDK and `genai.Client` resolved this.