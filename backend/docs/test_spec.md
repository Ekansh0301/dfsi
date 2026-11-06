# Test spec (Sprints 3 and 4)

What each Sprint 3 change does, which tests cover it, what it measurably changed, and what is still weak. Run everything with:

```bash
cd backend && pytest                       # backend: 191 tests
cd frontend && npm test && npm run typecheck && npm run build   # 33 tests, 8 more need the service
cd frontend && E2E_API_URL=http://localhost:8000 npm run test:e2e   # with the service running
```

Measured effects come from `results/model_comparison.md` (5 evaluation seeds of 3,000 made-up learners per simulator; settings chosen on tuning seed 100).

## Changes driven by Barabari's quiz format

| ID | Change | Tests | Effect | Still weak |
|---|---|---|---|---|
| S3-4 | Question types: true/false (guess 0.5), short answer (guess 0.05) | `tests/test_barabari.py` (`test_true_false_right_answer_is_weaker_evidence...`, `test_a_right_short_answer_is_strong_evidence`), `frontend/src/engine/__tests__/engine.test.ts` | A right true/false answer moves mastery less than a multiple-choice one | Guess rates are fixed, not fitted |
| S3-4 | Partial credit from points (short answers) | `test_partial_credit_mixes...`, `test_partial_credit_is_monotone...`, `test_score_overrides_is_correct` | A mark between 0 and 1 moves mastery between the wrong and right updates | The mark is trusted as given |
| S3-4 | Retakes count for less (0.5 to the power k minus 1) | `test_retakes_count_for_less` | Attempt 2 moves the estimate half as far | The decay 0.5 is a choice, not fitted |
| S3-4 | Barabari quiz importer and adapter endpoint | `tests/test_barabari.py` (validation, scoring, tags, events, endpoint, 422 cases) | Barabari's quiz JSON is read as is; the PDF's example quiz parses | `quiz_attempts` columns are assumed until Barabari shares them |
| S3-1 | Simulator: true/false, short answers, points, difficulty, retakes, answers remembered after the reveal | `tests/test_simulate.py` (sprint2 byte-identical, types, retakes, scores, reproducibility), `tests/test_dataset.py` | The Sprint 2 simulator is reproduced byte for byte; the saved dataset now has these fields | The story is still ours, not Barabari's data |
| S3-8 | Frontend: true/false questions, points, model choice | `engineClient.test.ts` (true/false event, `?model=`), `engine.test.ts` (same guess rates as the service) | Two true/false questions in modules 1 and 6; points shown in the quiz and on results | |
| S4-5 | Trainer marks short answers; the mark becomes partial credit | `tests/test_model.py` (`/v1/marked-answer`), `frontend/src/api/__tests__/marking.test.ts` | A written answer waits in the trainer's "To mark" list, then updates mastery by its mark | One short-answer question so far (module 2) |

## Model changes (improved model)

| ID | Change | Tests | Effect | Still weak |
|---|---|---|---|---|
| S3-2 | First-tag credit | `tests/test_model.py` (`test_first_tag_credit...`, `test_a_wrong_two_concept_answer_no_longer_blames...`) | See `results/model_comparison.md`: fitted slip and true-blocker rate | Second tags carry no evidence at all |
| S3-3 | Question difficulty (per-question slip and guess) | `test_harder_questions_slip_more...`, `test_difficulty_estimates_follow_correct_rates` | Higher next-answer AUC on the Barabari simulator | Needs answers per question; the service has none for our own questions yet |
| S3-5 | Prerequisite-aware learning rate | `test_learning_is_slower_while_an_observed_prerequisite_is_weak`, `test_unobserved_prerequisites_do_not_slow_learning` | More hidden blockers found, fewer missed gaps | Raises false alarms on its own |
| S3-6 | More evidence before a lesson | `test_one_borderline_answer_is_not_enough...`, `test_unobserved_concepts_are_never_a_gap...` | Fewer false alarms | Can delay a lesson by one quick check |
| S3-7 | Model switch (`?model=`, `CIRCUIT_COACH_MODEL`, `VITE_ENGINE_MODEL`) and promotion check | `test_health_reports...`, `test_a_request_can_choose_the_model`, `scripts/compare_models.py` | Both models served side by side | EdNet comparison still to run (raw files not on this machine) |

## Storage

| ID | Change | Tests | Effect | Still weak |
|---|---|---|---|---|
| S4-4 | Optional learner storage (`CIRCUIT_COACH_DB`, SQLite or PostgreSQL) | `tests/test_storage.py` (round trip, survives a restart, continues from the saved state, a sent state still wins, step log, Barabari `student_id`, stateless without storage) | State survives a service restart; every model step is logged | Only tested on SQLite here; PostgreSQL uses the same portable types |

## Sprint 4

| ID | Change | Tests or script | Result | Still weak |
|---|---|---|---|---|
| S4-1 | Edge cases: empty quiz, all "I'm not sure", a tag listed twice, a concept with no prerequisites, impossible values, non-finite numbers, resent requests | `tests/test_edge_cases.py` (33 cases, both models), `frontend/src/engine/__tests__/engine.test.ts` | A concept never answered is no longer a gap; bad input gets a 422, never a 500; with storage a resent request is applied once. Evaluation results unchanged | Without storage a resent request is applied again |
| S4-2 | Robustness: parameters across seeds, bounds, mis-tagged questions, a wrong concept graph | `scripts/robustness.py`, `results/robustness.md` | 25% mis-tagged questions cost 12 points of true blockers; 3 missing links cost 13.5 points of hidden blockers found; wrong extra links about 2 | Tags and the graph need a trainer's check |
| S4-3 | Calibration of predicted chances and mastery estimates | `scripts/calibration.py`, `results/calibration.md`, `results/calibration.png` | Next answer well calibrated (ECE 0.022 improved); mastery about 10 points high between 0.2 and 0.7 | No recalibration step yet |
| S4-6 | Failure analysis for both models, revised design doc, demo plan | `scripts/failure_analysis.py`, `docs/Technical_Design_Doc.md`, `docs/demo_plan.md` | Improved model: lessons on a known concept 41.8% to 18.4% (Barabari sim) | More blockers look fine |

## Unchanged guarantees

- Defaults reproduce the Sprint 2 baseline exactly (`test_defaults_keep_the_original_update`, `test_baseline_still_credits_every_tag`, `test_sprint2_config_reproduces...`).
- The committed contract matches the code (`tests/test_contract.py`).
- The Python and TypeScript curricula match (`tests/test_parity.py`).
- The demo scenarios end the same way with both models (`test_improved_model_keeps_the_demo_scenarios`, `journey.e2e.test.ts`).
