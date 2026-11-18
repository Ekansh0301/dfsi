# Test spec (Sprints 3 and 4, Hackathon 2)

What each Sprint 3 change does, which tests cover it, what it measurably changed, and what is still weak. Run everything with:

```bash
cd backend && pytest                       # backend: 239 tests
cd frontend && npm test && npm run typecheck && npm run build   # 174 tests, 8 more need the service
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
| S3-7 | Model switch (`?model=`, `CIRCUIT_COACH_MODEL`, `VITE_ENGINE_MODEL`) and promotion check | `test_health_reports...`, `test_a_request_can_choose_the_model`, `scripts/compare_models.py` | Both models served side by side | EdNet comparison done in Hackathon 2 (AUC 0.729 against 0.627); the improved model is now the service default |

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

## Hackathon 2

| Change | Tests | Result |
|---|---|---|
| Written answers in the answer review; error boundary | Checked in the browser (Module 2 preset) | No blank screen; "waiting for mark" or the trainer's mark |
| Placement shows no points | | "No marks" and no points on the placement check |
| Demo presets for the Module 1 and 2 checks | `presets.test.ts` | The true/false and short-answer demo steps are one click away |
| Health check on start-up; a down service costs a quick check per step | `engineClient.test.ts` (`shows 'checking'...`, `while the service stays down...`) | The top bar reflects the service; no 4 second wait per step while it is down |
| Mastery bands for trainers | Checked in the browser (escalation preset) | Needs work, Getting there, Strong at 0.6 and 0.8 |
| Finished lesson recorded on "Got it!" | `tests/test_storage.py` (`test_a_repeat_gap_with_stored_state...`, `test_got_it_rejects...`) | With storage on, a repeat gap gets a lesson not yet tried |
| Repeated answers in a Barabari attempt | `tests/test_barabari.py` (`test_endpoint_rejects_inconsistent_input`) | 422 instead of a 300% score |
| Concurrent copies of one request; a reused `request_id` | `tests/test_storage.py` (`test_copies_of_one_request...`, `test_a_request_id_reused...`) | Applied once; 409 for a different request |
| API key, browser origins, size limits | `tests/test_security.py` | 401 without the key when one is set; unknown sites get no CORS header; oversized requests 422 |
| Shipped parameters protected | `tests/test_shipped_params.py` | Fails if `fitted_params.json` drifts from the frozen version |
| Hindi messages, tips and labels | `marking.test.ts` (`a learner who reads Hindi...`) | The trainer's mark arrives in the learner's language |
| Neutral figure descriptions | `src/data/__tests__/figures.test.ts` | Every quiz figure described in both languages without naming an option |
| Listen button | `src/components/__tests__/listen.test.ts` | Indian voice preferred; hidden when the device has no voice for the language |
| Unfinished quiz answers kept | Checked in the browser | A reload returns to the same question with the answers given |
| Offline install | Checked on the built site | Service worker active; the app's script and styles cached on the first visit |
| Improved model as the service default | `tests/test_model.py` (`test_health_reports_the_default_and_available_models`, `test_a_request_can_choose_the_model`), `tests/test_storage.py` (`test_every_step_is_logged`), `engineClient.test.ts` (`shows the model the service uses by default`), `journey.e2e.test.ts` (service and browser engine agree) | A request without `?model=` is answered by the improved model; `?model=baseline` still works; the top bar shows the service's model; the demo scenarios give the same result as the browser fallback |
| Browser engine ported from the service: fitted parameters, both models, retakes, difficulty, evidence rule | `src/engine/__tests__/parity.test.ts` (120 journeys recorded from the service), `engine.test.ts`, `tests/test_parity.py` (the recording, the shared data files and the curriculum are current) | The live site, the fallback and the service answer alike; the Module 2 demo behaves as scripted with no service |
| Question id and attempt number sent by the app; one shared difficulty table | `tests/test_item_difficulty.py`, `engineClient.test.ts` | Difficulty reaches the served model; the table can be estimated from stored answers |
| The model as served, measured | `scripts/served_model_check.py`, `results/served_model.md` | 10 of 12 diagnosis measures clearly better than the baseline |
| Paired comparison, accuracy baseline | `tests/test_paired.py`, `tests/test_accuracy_engine.py` | Reports reproduce from the committed results |
| Continuous integration | `.github/workflows/tests.yml` | Engine, app and end-to-end tests on every push |

## Unchanged guarantees

- Defaults reproduce the Sprint 2 baseline exactly (`test_defaults_keep_the_original_update`, `test_baseline_still_credits_every_tag`, `test_sprint2_config_reproduces...`).
- The committed contract matches the code (`tests/test_contract.py`).
- The Python and TypeScript curricula match (`tests/test_parity.py`).
- The demo scenarios end the same way with both models (`test_improved_model_keeps_the_demo_scenarios`, `journey.e2e.test.ts`).
