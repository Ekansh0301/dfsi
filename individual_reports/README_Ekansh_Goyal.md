# Individual report: Ekansh Goyal

**Course:** DFSI 2026, Problem 3B (identifying what a learner needs next) | **Team:** Impact Theory | **Project:** Circuit Coach, Hackathon 2

## My contribution: true/false questions

Barabari's quizzes use true/false questions with points, so the app and the engine both had to support them properly.

- **The question type.** A true/false question has two options, True and False, shown in that natural order (other questions are shuffled). It carries a "True/False" tag and 5 points. We have two: one in Module 1 (safety) and one in Module 6 (earthing).
- **Weaker evidence in the engine.** A learner who does not know the answer still has a 50% chance of guessing right, so a correct true/false answer says much less than a correct multiple-choice one. I set this guess rate to 0.5 in the Python engine and in the browser engine, and a parity test checks they agree.
- **Points on screen.** The quiz shows each question's points and the results show points earned. The placement check does not, because it says "No marks".
- **Barabari's rules.** The importer rejects a true/false question that does not have exactly two options and one correct answer (`backend/circuit_coach/barabari.py`), and the simulator generates true/false questions.
- **The demo.** "Module 1 check (true/false)" shows the effect. One wrong true/false alone gives no lesson, because it is weak evidence and the learner did well in placement. Two wrong multiple-choice answers plus the true/false give the lesson "Safe isolation in 4 steps".

Tests: true/false evidence in `tests/test_barabari.py`, matching guess rates in `engine.test.ts`.

## Alongside it

I also worked on the app and the live site: the answer-review screen, the "Engine" label that checks the service on start-up, mastery bands for trainers (including the concept map), Hindi messages and labels, offline use and saving unfinished quizzes, and deploying the latest build to Vercel.

## Hackathon experience

The most useful part was running the real app instead of trusting the tests. A true/false question looked finished until we tried the demo and saw a single wrong answer produce nothing. That sent us back to understand why, and to explain it clearly rather than change the model to make the demo look better. Keeping the live site in step with the repository was also a lesson: a build that works locally is not the same as the site people see.

## Key learnings

- **A guess rate is a real assumption.** It decides how much one answer is worth. The same wrong answer should hurt a learner more on a question they could not guess.
- **Two copies of a model must agree.** We run the engine in Python and in the browser. Parity tests caught drift that would otherwise have shown up only when the service was down.
- **Explain surprising behaviour, do not hide it.** When the app does not recommend a lesson, there is usually a reason in the evidence, and the demo should say so.
- **Deployment is part of the work.** Version labels in the top bar and a repeatable build made it easy to check what was live.

## Where to look

`frontend/src/data/curriculum.ts` (`q_s4`, `q_e2`) | `frontend/src/learner/Quiz.tsx` | `frontend/src/engine/engine.ts` | `backend/circuit_coach/bkt.py` (guess rates) | `backend/circuit_coach/barabari.py`
