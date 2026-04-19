# Reflection — PawPal+ Applied AI System

## Limitations and Biases

The scheduling algorithm in PawPal+ is purely priority-based and greedy, which means it has real blind spots. It does not account for task dependencies — for example, a pet should be fed before receiving oral medication, but the scheduler has no way to enforce that ordering. It also has no awareness of time of day, so it might schedule an outdoor walk and an indoor grooming session back to back without considering that one requires daylight. The system treats all pets equally regardless of species, age, or health status, which means a senior dog and a young cat get the same scheduling logic even though their care needs are very different.

On the AI side, Gemini's explanations are only as good as the data the user enters. If a user assigns arbitrary priority numbers without much thought, the AI will explain those choices confidently even if they don't reflect what the pet actually needs. The system has no way to push back on unrealistic inputs. There is also no memory between sessions, so the AI cannot learn a user's patterns over time or notice that a task has been skipped repeatedly.

## Potential Misuse and Prevention

The most likely misuse is over-reliance. A user could treat Gemini's explanation as professional veterinary advice and skip tasks the scheduler excluded without fully understanding the consequences — for example, skipping a medication reminder because it didn't fit the time budget. To reduce this risk, the app always displays excluded tasks with a clear reason, and the AI is framed as a scheduling explainer rather than a medical authority. Adding a disclaimer near the AI explanation that reminds users to consult a vet for health-related decisions would be a meaningful next step.

A less obvious misuse is that the chat feature could be prompted to give advice outside of pet care entirely. The current prompt instructs Gemini to redirect off-topic questions, but a determined user could still get general information by framing questions as pet-related. A content filter or stricter system prompt would help in a production version.

## Surprises During Reliability Testing

The biggest surprise was how cleanly the fallback behavior worked once it was properly structured. Early in development, if the `GEMINI_API_KEY` was missing, the app would crash at import time rather than at the point where the API was actually called. Moving the key check into `GeminiAdvisor.__init__` and setting an `_enabled` flag meant the rest of the system never had to care whether AI was available — it just called the same methods and got a usable result either way. This made the mock-based tests much simpler to write and revealed that good error handling is really about designing the failure path as carefully as the success path.

Another surprise was that the AI explanations were noticeably better when excluded tasks were included in the prompt. Early versions only told Gemini what was scheduled, and the explanations felt incomplete. Adding the excluded tasks gave Gemini the full picture and the explanations became much more honest and useful — acknowledging trade-offs rather than just celebrating what made the cut.

## AI Collaboration

Throughout this project, Claude was used as a collaborative coding partner to scaffold the system architecture, write and debug code, and structure the test suite.

One instance where the AI gave a genuinely helpful suggestion was during the design of the `GeminiAdvisor` prompt for `explain_schedule()`. The suggestion to include excluded tasks in the prompt — not just the scheduled ones — was something that wasn't in the original plan. It made the AI explanations significantly more useful because Gemini could reason about what didn't fit and why, rather than just describing what did. That single change made the output feel like a real explanation rather than a summary.

One instance where the AI suggestion was flawed was the initial use of the `google.generativeai` package and the `GenerativeModel` class. The code worked at first but produced a `FutureWarning` during testing indicating that the entire package had been deprecated by Google and would no longer receive updates or bug fixes. The correct approach was to switch to the `google-genai` package and use `genai.Client` instead — something that required catching the warning, reading the deprecation notice, and updating both the requirements and the import structure. It was a good reminder that AI-generated code reflects its training data, which may not include the most recent library changes, and that testing output carefully is always necessary.