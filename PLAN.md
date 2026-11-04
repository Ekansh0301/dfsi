# Project plan: Circuit Coach to final submission

Team Impact Theory, DFSI 2026, Problem 3B (identifying what a learner needs next). Read `HANDOFF.md` first for what exists today and how to run it. This file says what is left and how we decide when each part is done.

## 1. Goal and scope

Deliver a working technical proof of concept (POC v1.0) and its evidence. The graded core is the engine: it estimates what a learner understands per concept, finds the concept that is really holding them back, and recommends one lesson. We improve the model, measure it against the baseline we already have, and package the result.

Not goals: a comparison of many models, grading answers (Barabari's Code Guru already does that), matching Barabari's exact course content, or a production system.

## 2. Schedule

The course dates below are the originals from the sprint plan. Sprint 3 slipped, so **replace these with the real dates once confirmed** and keep the order.

| Phase | Original dates | Course deliverables |
|---|---|---|
| Sprint 3 | 11 to 24 Oct | Improved POC v0.2, evidence of changes made in response to feedback, test and evaluation results, known limitations and priorities, test spec |
| Sprint 4 | 25 Oct to 7 Nov | Revised technical design doc (evaluation, failure analysis, limitations), near-complete POC v0.9, demo plan and evidence |
| Hackathon 2 | 7 Nov | POC v1.0 with all code and docs on GitHub, final technical design doc with final evidence |
| Sprint 5 | 8 to 14 Nov | NGO review. Final functional scope doc, design doc, technical design doc, slides, poster, demo video on GitHub. Final technical design doc, slides, poster and video on Moodle |
| Evaluations | 14, 18, 20 Nov | Formal demo 2, final assessment and defense, showcase |

## 3. Decisions already made

- **Model:** keep the per-concept mastery model (BKT) and extend it. A logistic or deep model predicts answers but gives no mastery state, which the root-cause walk and the 0.6 and 0.8 thresholds need.
- **Barabari:** we adapt only what changes the algorithm (retakes, points, true/false, short-answer scores as partial credit). Their format is in the PDF they sent; they grade assignments themselves. Concept tags are missing in their data, so tag at the unit level as a fallback, checked by a trainer.
- **Storage:** SQLite first, PostgreSQL by changing the connection URL (Barabari uses PostgreSQL).
- **Feedback from Hackathon 1:** instructors said it was good and asked for voice support back, with a natural voice.
- **Promotion rule:** the improved model becomes the default only if it beats the baseline on the made-up learners and narrows the EdNet gap, with all tests passing. The baseline stays selectable.

## 4. Work packages

Each package says where the work goes and when it is done. Owners are filled in by the team.

### Sprint 3 (POC v0.2)

| ID | Task | Where | Done when | Owner |
|---|---|---|---|---|
| S3-1 | Extend the simulator: retakes, points, true/false questions, per-question difficulty | `circuit_coach/simulate.py`, `dataset.py`, `tests/`, `docs/synthetic_data.md` | Same seed gives identical files; the dataset validator and tests cover the new fields; the saved dataset is regenerated | |
| S3-2 | Credit only the first concept tag on multi-concept questions | `circuit_coach/bkt.py`, `prediction.py` | Fitted slip near the true value (0.25 now, true about 0.09); fewer recommendations of a concept the learner knew (31.6% now) | |
| S3-3 | Per-question difficulty (item-specific slip and guess) | `bkt.py` | EdNet AUC up from 0.627, closer to per-question accuracy 0.721 | |
| S3-4 | Retake discounting, points as partial credit, true/false guess rate | `bkt.py`, `engine.py`, `api.py`, `docs/openapi.json`, `tests/test_contract.py` | Repeated attempts count for less; the contract carries `attempt_number`, points and question type; contract tests pass | |
| S3-5 | Prerequisite-aware learning rate (learning slower while a prerequisite is unmastered) | `bkt.py`, `engine.py` | Share of hidden blockers found above 61.9% | |
| S3-6 | Require more evidence before recommending a lesson | `engine.py` | False alarms below 31.9% with missed gaps not above 2.6% | |
| S3-7 | Model switch and promotion decision | `api.py`, `backend/results/`, `docs/evaluation.md` | Config or request flag selects baseline or improved; comparison tables saved; decision written down; tag `v0.2` | |
| S3-8 | Frontend: true/false and points in the quiz; show the engine mode | `frontend/src/`, `frontend/src/api/__tests__/` | Types, build and tests pass in API mode and with the service down | |
| S3-9 | Voice: pick a natural English and Hindi voice by ear, generate static audio, add a listen button hidden when a file is missing | `frontend/public/audio/`, a regeneration script | Audio plays on a phone-sized screen; changed text is flagged for regeneration; check the voice service's licence | |
| S3-10 | Test spec, evidence of changes, limitations | `backend/docs/test_spec.md`, `backend/docs/evaluation.md` | Each change lists its test, its measured effect and what is still weak | |
| S3-11 | Record the demo video | steps in `backend/docs/e2e_results.md` | Video covers the four demo scenarios and the service-down fallback | |

### Sprint 4 (POC v0.9)

| ID | Task | Where | Done when |
|---|---|---|---|
| S4-1 | Edge cases: all "I'm not sure", empty quiz, duplicate attempts, concept with no prerequisites, invalid input | `backend/tests/` | Each case has a test and a defined behaviour |
| S4-2 | Robustness: fitted parameters across seeds, parameter bounds, noisy tags and wrong or missing prerequisite links (via the simulator) | `backend/scripts/`, `backend/results/` | A short table shows how much diagnosis degrades, and what we do about it |
| S4-3 | Calibration check of the mastery numbers | `backend/scripts/`, `backend/results/` | A table or plot shows predicted against observed |
| S4-4 | SQLite storage of learners, PostgreSQL-compatible | `circuit_coach/`, `api.py` | State survives a restart; contract tests still pass; the stateless mode still works |
| S4-5 | Trainer scoring of short answers (a mark on a scale becomes partial credit) | `frontend/src/educator/`, `api.py` | A trainer can mark an answer and the engine uses it; optional language-model hint only if Barabari's interface shows no AI score |
| S4-6 | Revised technical design doc and demo plan | `backend/docs/Technical_Design_Doc.md` | Evaluation, failure analysis and limitations match the latest results |
| S4-7 | Freeze the model; tag `v0.9` | repo | No model changes after this tag |

### Hackathon 2 (POC v1.0)

Fix the top remaining issues, polish the demo flow, run all tests, capture the final evidence, finish the final technical design doc, push everything to GitHub, tag `v1.0`. No new features on this day.

### Sprint 5 (package and defend)

| ID | Task | Done when |
|---|---|---|
| S5-1 | Clean the code and READMEs, remove dead files | A new person can run everything from the README |
| S5-2 | Final documents on GitHub: functional scope doc, design doc, technical design doc | All three match what is built |
| S5-3 | Slides, poster, demo video | Problem, solution, technology and results connect in one story |
| S5-4 | NGO review preparation | A 10 minute walkthrough and the open questions for Barabari and Nirmaan |
| S5-5 | Moodle submission | Final technical design doc, slides, poster and video uploaded |
| S5-6 | Defense preparation | Answers ready for: why BKT, what the results do and do not show, what happens without real learner data |

## 5. How we work

- **Branches:** one branch per task, named by its ID (for example `s3-2-first-tag-credit`), and a short review before merging into `main`.
- **Checks before merging:** `cd backend && pytest`, `cd frontend && npm test && npm run typecheck && npm run build`. Frontend tests need `frontend/.env.local` moved aside, or one test fails.
- **Results:** every model change adds a table in `backend/results/`, produced by a script anyone can rerun.
- **Writing:** no em dashes or en dashes anywhere (the build checks the site and READMEs). Keep documents short and plain.
- **Commits:** a short plain message, under your own name.
- **Not committed:** raw EdNet files, course PDFs, anything with real learner data. The EdNet processed sample stays in `backend/data/` and is rebuilt from the dataset page when needed.

## 6. Open items

- Confirm the real dates and replace section 2.
- Barabari: the only optional request is an anonymised quiz-attempts export with scores only. We could also ask for view-only demo accounts to see their interface. Nothing else is needed.
- Nirmaan: we have no format or data from them yet.
- Who owns each task (the Owner column).
- Which voice service to use (decide by listening to samples).

## 7. Risks

| Risk | What we do |
|---|---|
| The improved model does not beat the baseline on EdNet | Report it honestly, keep the model if it wins on made-up learners where prerequisites exist, and explain that EdNet has no prerequisite graph |
| No real NGO learner data | State clearly that results are on made-up and EdNet data and that learning gains are not shown |
| Concept tags are missing in Barabari's data | Unit-level tags, checked by a trainer; the robustness test (S4-2) shows how much errors matter |
| Time runs short | Cut in this order: language-model hint, voice, SQLite. Never cut the model work or the evidence |
