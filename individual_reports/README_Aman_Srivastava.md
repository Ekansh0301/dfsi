# Individual report: Aman Srivastava

**Course:** DFSI 2026, Problem 3B (identifying what a learner needs next) | **Team:** Impact Theory | **Project:** Circuit Coach, Hackathon 2

## My contribution: short answers and trainer marking

Barabari's quizzes include written answers that an instructor marks. My part was making Circuit Coach handle them end to end.

- **Short-answer questions in the engine.** A right written answer is strong evidence of knowledge, because a lucky guess is very unlikely (5%, against 50% for true/false). This is in `backend/circuit_coach/bkt.py`.
- **Partial credit.** The trainer's mark (0, 1/4, 1/2, 3/4 or full) blends the "right" and "wrong" updates, so 1/4 lowers a learner's score only a little and full marks raise it.
- **The marking flow.** A written answer waits in the trainer console's **To mark** page and is not sent to the engine until it is marked. `POST /v1/marked-answer` then updates the learner and may recommend a lesson. The learner gets the mark in Messages, in Hindi or English.
- **The learner's view.** "See my answers" shows what the learner wrote and either "waiting for your trainer's mark" or the mark. Before, this screen crashed on written answers; I fixed it and added an error boundary so one broken screen cannot blank the app.
- **A demo that shows the effect.** In the Module 2 demo the learner answers three questions right and writes an answer. No lesson appears yet. When the trainer marks 1/4, the Ohm's law lesson appears; a full mark leaves no lesson. I changed the demo preset so Ohm's law starts borderline, since otherwise the mark never changed anything.

Tests: partial credit and marking in `tests/test_barabari.py` and `tests/test_model.py`, `marking.test.ts`, and the Module 2 case in `presets.test.ts`.

## Hackathon experience

Hackathon 2 was less about new features and more about finding what was weak. We reviewed the whole project, then fixed the problems one by one. For my area that meant noticing, by actually clicking through the app, that a written answer could blank the screen and that our own demo did not show what we claimed. I also integrated the team's work, ran the final checks, wrote the technical design document and tagged `v1.0`.

## Key learnings

- **Evidence is not equal.** A true/false answer, a multiple-choice answer and a marked written answer should move a learner's score by different amounts. Choosing those weights is a modelling decision, not a detail.
- **Humans in the loop need care.** Marking arrives later, so the system must behave sensibly before and after it, and a mark should add evidence, not silently undo a decision already shown to the learner.
- **Check claims against the real thing.** Simulating the engine told me one thing; running the real app showed the demo did something else. Both are needed.
- **Report honestly.** Comparing models run by run corrected our own "13 of 14 measures" claim to 12 of 14, and the remaining two (missed gaps) are not better. Saying so is part of the result.

## Where to look

`backend/circuit_coach/bkt.py`, `engine.py`, `api.py` (`/v1/marked-answer`) | `frontend/src/educator/EducatorApp.tsx` (To mark) | `frontend/src/learner/Loop.tsx` (answer review) | `backend/docs/Technical_Design_Doc.md`
