# Circuit Coach: Technical Design (POC v1.0)

**Team:** Impact Theory | **Problem 3B:** Identifying what a learner needs next
**Prototype:** https://dfsi.vercel.app/ | **Code:** `backend/` and `frontend/` in the project repository
**Document:** Final Technical Design Document (Hackathon 2, POC v1.0). Earlier versions: `docs/archive/Sprint4_Technical_Design_Doc.md` (Sprint 4, POC v0.9), `docs/archive/Sprint2_Technical_Design_Doc.md` (Sprint 2) and `docs/archive/Hack1_Technical_Design_Doc.md` (after Hackathon 1).

Circuit Coach finds what a vocational learner is stuck on after each short quiz, traces it back to the real cause, and recommends one short lesson; a trainer steps in when the learner is still stuck. The engine reads Barabari's quiz format. Compared run by run on made-up learners, the improved model is clearly better than the baseline on 12 of 14 measures and not clearly different on the other 2. With the same prerequisite walk, knowledge tracing finds 12 to 24 points more true blockers than plain accuracy. POC v1.0 adds reading aloud in English and Hindi, offline use and a set of fixes from a full project review.

## 1. Introduction

Our project, **Problem 3B: Identifying what a learner needs next**, works with Barabari Collective and Nirmaan, which run skilling and vocational programmes. Learners study in short sessions, often on their phones, and a misunderstanding can go unnoticed until it blocks later topics. Trainers with large batches cannot see who is struggling or with what. We use a basic electrician course (10 concepts, 6 modules) as the example.

## 2. Changes in response to feedback and review

### 2.1 Since Hackathon 1

| Feedback | From | What we changed | Where |
|---|---|---|---|
| Assess the way the NGO does: subjective assignments and quizzes, not only MCQs | Barabari | The engine reads Barabari's question types: true/false (weaker evidence), instructor-marked short answers (partial credit), points, and retakes (count for less). Trainers mark short answers in a "To mark" list | `bkt.py`, `barabari.py`, trainer console |
| Get the NGO's quiz format and build to it | Professor | Barabari shared their format; quizzes sit at unit level with a 60% pass mark, which maps onto our module quick checks and our 0.6 gap threshold | `docs/barabari_format.md` |
| Get the NGO's data format to assess the algorithm | Professor | An importer reads Barabari's quiz JSON as is; their data has no concept tags, so questions are tagged by unit with trainer overrides. An adapter endpoint lets their LMS send an attempt directly | `barabari.py`, `POST /v1/barabari/quiz-attempt` |
| Voice support, with a natural voice | Barabari, instructors | A listen button reads each question with its choices, each lesson step and the recommendation aloud, in the learner's language, with the device's own voices. It hides when the device has no voice for the language | `components/ListenButton.tsx` |
| Results to improve (our own evaluation) | Sprint 2 analysis | Improved model: first-tag credit, question difficulty, prerequisite-aware learning, more evidence before a lesson | Section 6 |

### 2.2 Hackathon 2: fixes from a full project review

| Found | Fix |
|---|---|
| "See my answers" after a short answer blanked the whole app | Written answers show the text and "waiting for mark" or the trainer's mark; an error boundary keeps one broken screen from taking down the rest |
| The headline "13 of 14 measures" mixed run-to-run spread with real differences | Run-by-run paired comparison with 95% intervals (`results/paired_comparison.md`); the claim is now 12 clearly better, 2 not clearly different |
| Re-running the documented evaluation overwrote the shipped model parameters and silently reverted the improved model to the baseline's | Scripts write fits to `results/`; the shipped file changes only with `--write-service-params`, and a test checks it against the frozen version |
| With storage on, a repeat gap recommended the same lesson again | `POST /v1/got-it` takes the finished lesson (`content_id`) and records it in `tried` |
| A Barabari attempt answering one question six times scored 300% | Repeated answers are rejected (422) |
| Copies of one request arriving together were applied several times; a reused `request_id` silently returned the old answer | Unique request key per learner and step, state and log saved in one transaction; a reused key with a different request gets a 409 |
| The service accepted any origin, any caller and requests of any size | Optional API key, browser origins limited to the prototype, size limits on every list |
| The top bar said "Engine: API" before the service had answered | A health check on start-up; a down service costs a quick check per step instead of the full 4 second timeout |
| Hindi learners got the trainer's mark, tips and some labels in English; screen-reader descriptions of quiz figures named the answer | Messages, tips and labels in the learner's language; neutral figure descriptions in both languages, checked by a test |
| Trainers saw mastery as exact percentages, though mid-range estimates run high (6.5) | Bands at the engine's own thresholds: Needs work, Getting there, Strong |

## 3. Technical specification and architecture

**Inputs:** a learner's answers (concept tags, right or wrong, "I'm not sure", question type, a mark for short answers, attempt number), the concept graph, and the lessons per concept.
**Outputs:** a mastery probability per concept and at most one recommendation: `concept_id`, `observed_concept_id`, `chain`, `strong_concept_id`, `diagnostic_text` (English and Hindi), `recommended_content_id`, `repeat_gap`, `created_at`. Schemas: [api_contract.md](api_contract.md), [openapi.json](openapi.json).

![Architecture diagram](architecture.svg)

| Component | Role |
|---|---|
| Learner app and trainer console (React, `frontend/`) | Onboarding, quick checks with multiple choice, true/false and short answers; one recommended lesson; listen button; "Got it!" and "I'm still stuck"; escalation queue, cohort gaps, short answers to mark |
| Learner store (`mockServer.ts`) | Learner records and escalations in the browser's `localStorage`, shared across tabs and the side-by-side demo; unfinished quiz answers are kept across a reload |
| Offline support (`public/sw.js`, `manifest.webmanifest`) | The prototype installs on a phone and opens with no signal; the in-browser engine needs no network |
| Engine client (`engineClient.ts`) | Checks the service on start-up, sends the model steps, falls back to the in-browser engine on any failure or after 4 seconds |
| Engine service (FastAPI, `backend/circuit_coach/`) | Trace, root cause, recommend; two models (baseline, improved); optional storage, API key and size limits |
| Barabari adapter (`barabari.py`) | Reads Barabari's quiz and attempt JSON, tags questions with concepts, turns attempts into events |
| Storage (`storage.py`, optional) | With `CIRCUIT_COACH_DB` set: each learner's latest state and a log of every model step, on SQLite or PostgreSQL; a resent request is applied once |
| Offline code (`backend/scripts/`) | Simulators, datasets, fitting, model comparison, paired comparison, accuracy baseline, robustness, calibration, failure analysis |
| Continuous integration (`.github/workflows/tests.yml`) | Engine tests, app typecheck, tests and build, and the end-to-end journey against the running service, on every push |

| Endpoint | Purpose |
|---|---|
| `POST /v1/onboarding` | Seed a new learner from experience and the placement quiz |
| `POST /v1/quiz-result` | Update the model from a quick check; return at most one recommendation |
| `POST /v1/got-it` | Learning step after "Got it!"; records the finished lesson |
| `POST /v1/marked-answer` | A trainer's mark for a short answer, as partial credit |
| `POST /v1/barabari/quiz-attempt` | One attempt in Barabari's own format: recommendation and quiz score |
| `GET /v1/learners/{id}/state` | A saved learner state (storage on) |
| `GET /v1/concepts`, `GET /health` | Concept graph and lessons; service status, default and available models |

Every POST accepts `?model=baseline|improved`. With storage on, it also accepts `learner_id` (continue from the saved state) and `request_id` (a resent request is applied once). Settings: `CIRCUIT_COACH_MODEL`, `CIRCUIT_COACH_DB`, `CIRCUIT_COACH_API_KEY`, `ALLOWED_ORIGINS` (`backend/README.md`).

## 4. The engine

1. **Trace.** One Bayesian Knowledge Tracing model per concept (mastered or not), with starting mastery, learning, slip and guess fitted by EM. After each answer the estimate is updated by Bayes' rule, then learning is applied. "I'm not sure" is a wrong answer with almost no chance of a lucky guess. True/false answers allow a 50% guess, short answers 5%. A marked short answer (0 to 1) mixes the right-answer and wrong-answer updates. Attempt k of a retaken quiz counts with weight 0.5 to the power k minus 1, because Barabari reveals answers after 3 attempts.
2. **Find the gap.** Among the concepts the quick check assessed, a concept with at least one answer and mastery below 0.6 is a gap; the most advanced one is the observed gap.
3. **Find the root cause.** Walk back to the weakest prerequisite that has been answered and is also below 0.6, and repeat.
4. **Recommend.** The first lesson for the root cause that the learner has not tried. A failed follow-up check after "Got it!" gives a repeat-gap recommendation with a different lesson and flags the trainer.

**The improved model** adds four options, tuned on a separate seed:

| Option | What it does |
|---|---|
| First-tag credit | A question tagged with several concepts updates only its first, main concept |
| Question difficulty | Slip and guess shift per question by its difficulty, estimated from training answers |
| Prerequisite-aware learning | Learning runs slower (down to half) while observed prerequisites look weak |
| More evidence before a lesson | A lesson needs 2 answers on the concept, unless its mastery is below 0.4 after one |

The baseline stays the service default (section 7); either model is selectable per request, for the whole service (`CIRCUIT_COACH_MODEL`) or for the prototype (`VITE_ENGINE_MODEL`). The model has been frozen since tag `v0.9`: nothing in POC v1.0 changes how mastery is estimated.

## 5. Data and evaluation design

| Dataset | What it is | What it can test |
|---|---|---|
| Made-up learners, Sprint 2 simulator | 3,000 learners per run, hidden mastery known, multiple choice only | Next-answer prediction and diagnosis against the truth |
| Made-up learners, Barabari simulator | As above, plus true/false, short answers, points, question difficulty, retakes of failed checks and answers remembered after the reveal | The same, under Barabari's format |
| EdNet KT1 | 14,460 real students, 189 concept tags, 357,756 test answers (1,765,406 in the full sample) | Next-answer prediction only |
| Barabari sample | One unit quiz in Barabari's JSON with made-up attempts | The importer and the adapter endpoint |

Splits are by learner (70:30 for made-up learners, 80:20 for EdNet). Measures: AUC, accuracy, log loss and RMSE for the next answer; for diagnosis, gap F1, whether the recommendation is a true blocker, hidden-prerequisite blockers found, lessons on a concept the learner knew, missed gaps and false alarms. Settings are chosen on tuning seed 100; results are on evaluation seeds 0 to 4. Model comparisons are paired by seed (both models see the same learners) with 95% intervals over the 5 runs. No real NGO learner data exists yet.

## 6. Results

### 6.1 Improved model against the baseline (5 runs of 3,000 made-up learners)

| Measure | Sprint 2 sim: baseline | improved | paired difference (95% interval) | Barabari sim: baseline | improved | paired difference (95% interval) |
|---|---|---|---|---|---|---|
| Next-answer AUC | 0.688 | 0.694 | +0.006 (+0.003 to +0.010) | 0.672 | 0.701 | +0.029 (+0.022 to +0.036) |
| Recommendation is a true blocker | 59.2% | 68.1% | +8.9 pts (+7.0 to +10.8) | 47.2% | 55.5% | +8.3 pts (+4.6 to +12.0) |
| Hidden-prerequisite blocker found | 61.9% | 69.3% | +7.5 pts (+4.9 to +10.0) | 49.0% | 58.3% | +9.3 pts (+4.5 to +14.1) |
| Lesson on a concept the learner knew | 33.9% | 18.0% | -15.9 pts (-19.9 to -11.8) | 41.9% | 26.6% | -15.2 pts (-22.8 to -7.6) |
| Missed gaps | 2.6% | 3.5% | +0.9 pts (-1.6 to +3.3) | 6.4% | 6.3% | -0.1 pts (-1.5 to +1.3) |
| False alarms | 31.9% | 24.2% | -7.7 pts (-12.2 to -3.2) | 38.2% | 30.7% | -7.5 pts (-10.8 to -4.3) |

Gap F1 is also clearly better on both (+0.9 and +2.2 points). Missed gaps are within the noise overall, but on the Sprint 2 simulator the improved model misses more in 4 of the 5 runs (median +1.5 points): the baseline's 2.6% average comes from one run at 6.4%, and in the other four it misses 1.3% to 2.1%. First-tag credit gives the largest gain; question difficulty lifts prediction where questions differ; prerequisite-aware learning wins back missed gaps; the evidence rule cuts false alarms. Full ablation: `results/model_comparison.md`; paired tables: `results/paired_comparison.md`.

### 6.2 Does knowledge tracing earn its place?

BKT without the prerequisite walk finds fewer true blockers than "study what you got wrong", so we gave the same walk, threshold and lesson choice to a much simpler estimate, the learner's smoothed accuracy so far ((right + 1) / (answers + 2)):

| Method (true blocker, hidden blocker found) | Sprint 2 sim | Barabari sim |
|---|---|---|
| Study what you got wrong | 31.2%, 7.4% | 32.8%, 7.5% |
| Accuracy + prerequisite walk | 44.0%, 43.4% | 34.7%, 35.2% |
| BKT baseline + prerequisite walk | 59.2%, 61.9% | 47.2%, 49.0% |
| BKT improved model | 68.1%, 69.3% | 55.5%, 58.3% |

The walk on plain accuracy recovers part of the gain; BKT recovers the rest. BKT finds 12 to 24 points more true blockers than accuracy with the same evidence rule and recommends 18 to 34 points fewer lessons on concepts the learner already knew, because accuracy never forgets an early wrong answer. Accuracy misses 0 to 3 points fewer gaps, since one wrong answer is enough for it to call a gap. Details: `results/accuracy_baseline.md`.

### 6.3 Real data: EdNet (Sprint 2 result)

Per-question accuracy (AUC 0.721) beats fitted BKT (0.627; 0.641 with the first tag only), because BKT ignores question difficulty. The improved model adds question difficulty, but the EdNet comparison has not been rerun: the raw files are not in the repository.

### 6.4 Robustness (Barabari simulator)

| Condition | Model | True blocker | Hidden blocker found | Missed gaps | False alarms |
|---|---|---|---|---|---|
| Correct tags and graph | baseline | 44.7% | 47.1% | 6.3% | 38.0% |
| | improved | 54.1% | 56.8% | 7.0% | 29.7% |
| 10% of questions mis-tagged | baseline | 38.5% | 42.4% | 5.2% | 42.7% |
| | improved | 48.9% | 53.4% | 8.1% | 31.8% |
| 25% of questions mis-tagged | baseline | 32.8% | 35.1% | 4.1% | 52.8% |
| | improved | 42.1% | 44.5% | 8.5% | 36.0% |
| 3 prerequisite links missing | improved | 47.7% | 43.2% | 7.2% | 29.3% |
| 3 wrong prerequisite links added | improved | 52.0% | 55.0% | 6.9% | 29.8% |

The improved model finds more blockers and raises fewer false alarms than the baseline in every condition, but it misses more gaps in every condition, and the difference grows with mis-tagging (8.5% against 4.1% at 25%). Missing links hurt most; wrong extra links barely matter. With first-tag credit, only 4% to 6% of fitted parameters sit on a bound (16% to 21% before). Details: `results/robustness.md`.

### 6.5 Calibration

Next-answer probabilities are well calibrated (expected calibration error 0.022 improved, 0.034 baseline). Mastery estimates run about 10 points high between 0.2 and 0.7 (error 0.07): at an estimate near 0.6 about half the learners truly know the concept. The ranking of learners is good (mastery AUC 0.79 to 0.85), so recommendations hold. Trainers now see bands at the engine's thresholds rather than percentages; a recalibration step is future work. Details: `results/calibration.md`.

### 6.6 Failure analysis (hidden-prerequisite cases)

| What happened | Sprint 2 sim: baseline | improved | Barabari sim: baseline | improved |
|---|---|---|---|---|
| Found the true blocker | 66.6% | 72.2% | 45.7% | 59.8% |
| Recommended a concept the learner knew | 20.2% | 13.0% | 41.8% | 18.4% |
| Blocker asked about but looked fine | 8.5% | 9.8% | 4.2% | 14.9% |
| Real gap, but the blocker was further upstream | 2.9% | 4.0% | 3.3% | 4.4% |
| No gap seen | 1.9% | 0.9% | 4.9% | 2.5% |

First-tag credit stops a wrong answer on a two-concept question from blaming both concepts. The cost is that a prerequisite is judged on fewer answers, so more blockers look fine.

## 7. What worked, what did not, and the promotion decision

**Worked**

- Reading Barabari's format changed the evidence the model uses without changing the product's flow.
- The improved model is clearly better on 12 of 14 measures on both simulators, paired by run.
- Knowledge tracing adds clear value over plain accuracy with the same walk (6.2).
- The engine handles edge cases with a defined behaviour (empty quiz, all "I'm not sure", impossible values, duplicate and concurrent requests), and the browser engine follows the same rules.

**Did not work, or not yet**

1. The improved model misses more gaps than the baseline in most runs on the Sprint 2 simulator and under mis-tagging; the plan's target was no more than the baseline's 2.6%.
2. The EdNet comparison for the improved model has not been run.
3. Mastery estimates are over-confident in the middle range.
4. Concept tags in Barabari's data do not exist yet; unit-level tags put several concepts on every question, the case first-tag credit handles worst.

**Promotion decision.** The baseline stays the service default because of points 1 and 2. The improved model is fully available and tested (`?model=improved`, `CIRCUIT_COACH_MODEL=improved`, `VITE_ENGINE_MODEL=improved`) and is our recommendation once the EdNet check is run, since with correct tags it misses about 1 to 2 points more gaps while sending far fewer learners to the wrong lesson (more gaps are missed under heavy mis-tagging, 6.4). The decision is recorded in `docs/evaluation.md`.

## 8. POC v1.0 status

| Part | State |
|---|---|
| Learner app and trainer console (English and Hindi) with true/false, short answers, marking, listen button, offline use | Working |
| Engine service with two models, Barabari adapter, marked answers, optional storage, API key and size limits | Working; 216 backend tests |
| Prototype with fallback to the browser engine | Working; 42 frontend tests, 8 more end-to-end with the service running |
| Made-up learners in two formats, Barabari sample, EdNet loader | Working |
| Evaluation: model comparison (also paired), accuracy baseline, robustness, calibration, failure analysis | Reproducible, reports in `backend/results/` |
| Continuous integration on every push | `.github/workflows/tests.yml` |
| Demo plan | `docs/demo_plan.md` |
| Demo video | Open |
| EdNet comparison of the improved model | Future work |

## 9. Limitations

- No real learner data from the NGOs: results reflect the simulators' assumptions and EdNet's different subject and population.
- Nothing yet shows that learners learn more.
- The parameters the service ships with were fitted on one run of the Sprint 2 simulator (2,100 made-up learners, multiple choice only); 4 of the 10 baseline concepts sit on the slip bound of 0.30. They are placeholders until real answers exist.
- Barabari's attempt records are read in an assumed shape until they share theirs (`docs/barabari_format.md`).
- The improved model's settings were tuned on made-up learners.
- Escalations and trainer replies live in the browser's storage, not in the service.
- The listen button uses the voices installed on the device; many desktops have no Hindi voice, and voice quality varies. Pre-recorded natural audio is the next step.
- Two copies of the engine (Python and the browser) are kept in step by tests; the browser copy has only the baseline model.
