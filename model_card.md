# Model Card — PawPal+ AI System

## Model Overview

**System name:** PawPal+
**AI model used:** Gemini 2.0 Flash (via Google Generative AI API)
**Role of AI in system:** Gemini serves as the explanation and reasoning layer. It receives structured schedule data from the Python scheduler and returns natural language explanations of why tasks were prioritized, as well as answers to follow-up pet care questions from the user.
**Developer:** Anijah
**Course:** AI110 — Final Project

---

## Intended Use

PawPal+ is designed to help pet owners plan and understand their daily pet care routines. The AI component is intended to make the schedule explainable in plain language and to answer general pet care questions in context. It is not intended to replace veterinary advice.

---

## AI Collaboration

### How AI was used during development

Claude (Anthropic) was used as a collaborative coding partner throughout this project. It helped scaffold the system architecture, write and debug Python code, design the test suite, and structure the README and reflection documents. All code was reviewed, tested, and verified by the developer before being committed.

### One instance where AI gave a helpful suggestion

When designing the prompt for `GeminiAdvisor.explain_schedule()`, Claude suggested including the list of excluded tasks in the prompt — not just the scheduled ones. This was not in the original plan. The result was significantly better AI explanations: Gemini could reason about what didn't fit in the time budget and why, rather than only describing what was scheduled. This made the output feel like a genuine trade-off explanation rather than a simple summary.

### One instance where AI gave a flawed or incorrect suggestion

Claude initially suggested using the `google.generativeai` package with the `GenerativeModel` class to integrate Gemini. This code ran but produced a `FutureWarning` during testing indicating the entire package had been deprecated by Google and would no longer receive updates or bug fixes. The correct solution was to switch to the `google-genai` package and use `genai.Client` instead. This required updating both `requirements.txt` and the import structure in `pawpal_system.py`. It was a clear reminder that AI-generated code reflects its training data, which may not include the latest library deprecations, and that testing output carefully is always necessary.

---

## Biases and Limitations

### Algorithmic biases
- The greedy priority scheduler always favors high-priority tasks regardless of duration. A short low-priority task that could fill remaining time is always skipped in favor of nothing, even when it would fit easily. This is a known limitation of the greedy approach.
- The system has no awareness of species-specific needs. A senior dog and a young kitten receive identical scheduling logic despite having very different care requirements.
- Task dependencies are not modeled. The scheduler cannot enforce that feeding must happen before medication, or that outdoor tasks require daylight.

### AI biases
- Gemini's explanations are confident by default. If a user enters low-quality or arbitrary priority numbers, the AI will explain those choices as if they were well-reasoned. The system cannot push back on poor inputs.
- The AI has no memory between sessions. It cannot learn a user's patterns, notice skipped tasks, or adjust recommendations over time.
- Gemini responses may reflect general pet care conventions that do not apply to every breed, species, or individual animal.

---

## Potential Misuse and Safeguards

**Risk 1 — Over-reliance on AI explanations:** A user could treat Gemini's output as veterinary advice and skip excluded tasks without understanding the consequences. Safeguard: excluded tasks are always displayed with a clear reason, and the app does not frame the AI as a medical authority.

**Risk 2 — Off-topic chat use:** The follow-up chat feature could be steered toward topics unrelated to pet care. Safeguard: the system prompt instructs Gemini to redirect off-topic questions back to pet care. A stricter content filter would be appropriate in a production version.

**Risk 3 — API key exposure:** If the `.env` file were accidentally committed to GitHub, the Gemini API key would be exposed. Safeguard: `.env` is listed in `.gitignore` and never committed. The app also runs safely without a key using the fallback explanation.

---

## Testing Results

**Test suite:** `test_pawpal.py`
**Total tests:** 25
**Passed:** 25
**Failed:** 0
**Runtime:** ~3 seconds

### What was tested
- Task completion and recurring logic
- Task addition, editing, and validation
- Priority-based sorting
- Time budget enforcement
- Multi-pet task aggregation
- Category constraint filtering
- Completed task exclusion
- `to_dict()` serialization for AI prompt building
- `GeminiAdvisor` disabled state and fallback behavior
- Scheduler explanation methods before and after plan generation

### How AI tests were handled
All AI layer tests use `unittest.mock.patch.dict` to remove the `GEMINI_API_KEY` from the environment, forcing `GeminiAdvisor` into disabled mode. This means no real API calls are made during testing, keeping the suite fast and deterministic while still verifying that fallback content is correct and the system never crashes when the API is unavailable.

### Known gaps
- No tests for the multi-turn chat history behavior
- No tests for the case where Gemini returns an empty or malformed response
- The greedy scheduler is not tested against an optimal solution to measure how much value it leaves on the table

### What surprised me
The mock-based tests revealed that early versions of `GeminiAdvisor` would throw an exception at import time if the API key was missing, rather than at the point of the actual API call. This would have caused the entire app to crash on startup for anyone without a key. Moving the key check into `__init__` and setting `_enabled = False` fixed this and made the fallback path clean and testable. Good error handling means designing the failure path as carefully as the success path.