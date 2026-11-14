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
- **Promotion rule:** the improved model becomes the default only if it beats the baseline on the made-up learners and narrows the EdNet gap, with all tests passing. The baseline stays selectable. **Outcome (Hackathon 2):** both conditions are met for the EdNet part and the improved model beats the baseline on 12 of 14 measures (the other 2 are not clearly different), so it was made the default.

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

## 4b. Status on 6 November 2026

Branch `sprint3-barabari`, one commit per step. Details: `backend/docs/test_spec.md`, `backend/docs/evaluation.md`, `backend/docs/barabari_format.md`.

| ID | State |
|---|---|
| S3-1 | Done. The Barabari simulator (true/false, short answers, points, difficulty, retakes) is the new default for the saved dataset; the Sprint 2 simulator is still reproduced byte for byte |
| S3-2, S3-3, S3-5, S3-6 | Done as options of one improved model. Compared run by run on made-up learners it is clearly better on 12 of 14 measures and not clearly different on missed gaps (3.5% against 2.6% on the Sprint 2 simulator, worse in 4 of 5 runs; target: not above 2.6%) |
| S3-4 | Done: question types, partial credit, retake discount, Barabari quiz importer and adapter endpoint |
| S3-7 | Model switch done (`?model=`, `CIRCUIT_COACH_MODEL`, `VITE_ENGINE_MODEL`). EdNet comparison done in Hackathon 2 (AUC 0.729 against 0.627); promotion not decided: the missed-gaps target above is the open point |
| S3-8 | Done: true/false questions and points in the quick checks; the top bar shows the model |
| S3-9 | Done in Hackathon 2 with the device's own voices (no audio files, no outside service); pre-recorded natural audio is future work |
| S3-10 | Done: `backend/docs/test_spec.md` |
| S3-11 | Open: demo video |
| S4-4 | Done: optional SQLite or PostgreSQL storage |
| S4-5 | Done: short answers go to a To mark list; the trainer's mark becomes partial credit |

## 4c. Status of Sprint 4 on 6 November 2026

| ID | State |
|---|---|
| S4-1 | Done: `backend/tests/test_edge_cases.py` |
| S4-2 | Done: `backend/results/robustness.md` |
| S4-3 | Done: `backend/results/calibration.md` (mastery estimates run about 10 points high in the middle range) |
| S4-4, S4-5 | Done in Sprint 3 |
| S4-6 | Done: `backend/docs/Technical_Design_Doc.md` (Sprint 4), `backend/docs/demo_plan.md`; earlier version archived |
| S4-7 | Done: model frozen and tagged `v0.9`. The baseline stayed the service default at the freeze (the improved model became the default in Hackathon 2). Known limits at the freeze: missed gaps on the Sprint 2 simulator 3.5% (target 2.6%) |

**Update (Hackathon 2):** the EdNet comparison for the improved model was run (download EdNet KT1 into `backend/data/raw/`, then `python scripts/compare_models.py`): AUC 0.729 against 0.627 for the baseline. The promotion decision is now the team's.

## 4d. Status of Hackathon 2 on 14 November 2026

POC v1.0. Details: `backend/docs/Technical_Design_Doc.md` (final), `backend/docs/test_spec.md` (Hackathon 2 section), `HANDOFF.md`.

| Task | State | Owner |
|---|---|---|
| Promotion decision, paired per-seed comparison with 95% intervals | Done: `results/paired_comparison.md`; EdNet run (AUC 0.729 against 0.627). Improved model made the service default | Aman |
| Shipped model parameters protected from re-runs | Done: `--write-service-params`, `tests/test_shipped_params.py` | Aman |
| Backend fixes: repeat gap with storage, duplicate Barabari answers, concurrent resent requests | Done, with tests | Aman |
| API key, CORS limited to known sites, size limits | Done, `tests/test_security.py` | Aman |
| Accuracy baseline with the same prerequisite walk | Done: `results/accuracy_baseline.md` | Aman |
| Continuous integration and Docker | Written; not yet run on GitHub (see section 6) | Aman |
| Final technical design doc (v1.0) | Done; Sprint 4 version archived | Aman |
| App fixes: answer review, error boundary, placement points, demo presets, tap targets, health check, progress text | Done | Ekansh's list, done in this session |
| Voice, mastery bands, Hindi and accessibility fixes, offline use, saved quiz progress, build version | Done | Ekansh's list, done in this session |
| Live prototype on the latest `main` | Done on 14 November; redeploy after every merge | Ekansh |
| Out-of-date documents | Done: `HANDOFF.md`, `backend/docs/e2e_results.md`, this file | Praveen's list |
| README results summary | Done: top of `README.md` | Divesh's list |
| README check from a fresh clone | Done on 14 November: backend install and 216 tests, frontend install, typecheck, 42 tests and build, and the service starts, all from the README steps. The Docker steps could not be tried (no Docker on the test machine). Note: the tests need the `eval` extras, so use `pip install -e ".[eval,dev]"` | Praveen |
| Slides, poster, demo video | Open (poster numbers: 216 backend plus 42 frontend tests, "12 of 14 measures") | Praveen, Divesh |
| Demo rehearsal, tag `v1.0` | Open | All, Aman |

## 5. How we work

- **Branches:** one branch per task, named by its ID (for example `s3-2-first-tag-credit`), and a short review before merging into `main`.
- **Checks before merging:** `cd backend && pytest`, `cd frontend && npm test && npm run typecheck && npm run build`. Frontend tests pass with or without `frontend/.env.local`.
- **Results:** every model change adds a table in `backend/results/`, produced by a script anyone can rerun.
- **Writing:** no em dashes or en dashes anywhere (the build checks the site and READMEs). Keep documents short and plain.
- **Commits:** a short plain message, under your own name.
- **Not committed:** raw EdNet files, course PDFs, anything with real learner data. The EdNet processed sample stays in `backend/data/` and is rebuilt from the dataset page when needed.

## 6. Open items

- Confirm the real dates and replace section 2 (Hackathon 2 and Sprint 5 are in progress as of 14 November 2026).
- Barabari: the only optional request is an anonymised quiz-attempts export with scores only. We could also ask for view-only demo accounts to see their interface. Nothing else is needed.
- Nirmaan: we have no format or data from them yet.
- Owners of the Sprint 5 tasks (see 4d for Hackathon 2).
- GitHub Actions did not run on the personal repository because of a billing lock on that account; fix it in the account's billing settings.

## 7. Risks

| Risk | What we do |
|---|---|
| The improved model does not beat the baseline on EdNet | Report it honestly, keep the model if it wins on made-up learners where prerequisites exist, and explain that EdNet has no prerequisite graph |
| No real NGO learner data | State clearly that results are on made-up and EdNet data and that learning gains are not shown |
| Concept tags are missing in Barabari's data | Unit-level tags, checked by a trainer; the robustness test (S4-2) shows how much errors matter |
| Time runs short | Cut in this order: language-model hint, voice, SQLite. Never cut the model work or the evidence |
