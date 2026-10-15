# Circuit Coach: Technical Design (revised)

**Team:** Impact Theory | **Problem 3B:** Identifying what a learner needs next
**Prototype:** https://dfsi.vercel.app/ | **Code:** `backend/` and `frontend/` in the project repository
**Document:** Sprint 2 Technical Design Document, revised after the Hackathon 1 issues (T1 to T7) were completed

This version replaces the one submitted to the instructors. Section 10 lists what changed and why.

## 1. Introduction

Our project, **Problem 3B: Identifying what a learner needs next**, works with Barabari Collective and Nirmaan, which run skilling and vocational programmes. Learners there study in short sessions, often on their phones, and learning happens across classes, videos and practice. Because of this, a learner may not realise they have misunderstood a concept until much later. Trainers, who look after large batches, cannot always tell who is struggling or with what.

**Circuit Coach** is our response. After each short quiz, it works out which concept a learner is finding difficult, suggests one short lesson to review it, and brings in the trainer if the learner is still stuck. We use a basic electrician course as the example.

In Sprint 1 we designed the product and built a clickable prototype of the learner app and the trainer console. Its "intelligence" was a simple stand-in running in the browser. This document covers the real technical core: the engine that estimates what each learner understands and decides what they should do next, and how well it performs.

## 2. Purpose and sprint activities

The sprint asked for five activities. This is where each one lives:

| Activity | What we did | Where |
|---|---|---|
| Define technical architecture and evaluation criteria | Architecture, data flow and API contract; evaluation design, metrics and baselines | Sections 3 and 5, `backend/docs/architecture.md`, `api_contract.md`, `evaluation.md` |
| Set up data, models, algorithms or processing pipeline | Made-up learner generator with saved datasets, the EdNet loader, BKT with EM fitting, the evaluation pipeline | `circuit_coach/simulate.py`, `dataset.py`, `bkt.py`, `ednet.py`, `scripts/` |
| Implement the hardest technical component first | The knowledge-tracing and recommendation engine, as a service | `circuit_coach/engine.py`, `api.py` |
| Establish a baseline result | Standard BKT plus a prerequisite walk, compared with simple baselines on made-up and real data | Section 6, `backend/results/` |
| Prepare the component for a focused Hack 1 build | Issues T1 to T7 completed, documented and tested; improvement candidates identified | Sections 8 and 9 |

The baseline is standard Bayesian Knowledge Tracing (BKT), one model per concept, with a simple walk back through prerequisites. We kept it deliberately plain so later improvements can be measured against it.

## 3. Technical specification and architecture

**Inputs:** a learner's answers (concept tags, correct or not, "I'm not sure"), the concept graph, and the lessons available per concept.
**Outputs:** a mastery probability per concept, and one recommendation with `concept_id`, `observed_concept_id`, `chain`, `diagnostic_text`, `recommended_content_id`, `repeat_gap` and `created_at`. The exact schemas are in [api_contract.md](api_contract.md) and [openapi.json](openapi.json).

![Architecture diagram](architecture.svg)

*Components. Dataset and evaluation code is offline; only the engine service runs when learners use the app.* The component and sequence diagrams are in [architecture.md](architecture.md).

| Component | Role |
|---|---|
| Learner app and trainer console (React, `frontend/`) | Onboarding, quick checks, one recommended lesson, "Got it!" and "I'm still stuck"; escalation queue and cohort gaps |
| Learner store (`mockServer.ts`) | Holds each learner's record (answers, mastery, tried lessons, re-checks, escalations, messages) in the browser's `localStorage` |
| Engine client (`engineClient.ts`) | Sends the three model steps to the service when `VITE_API_URL` is set; falls back to the in-browser engine on any failure |
| Engine service (FastAPI, `backend/circuit_coach/`) | Trace, root cause, recommend; stateless |
| Offline code (`backend/scripts/`) | Simulator, dataset files, EdNet loader, fitting, comparison and failure analysis |

**Design decisions**

- **Stateless service.** Each request carries the learner's model state (`mastery`, `observations`, `tried`) and returns the updated state. The engine is easy to test and to call from the prototype. The service stores nothing; learner records live in the browser. Server-side storage (SQLite first, PostgreSQL by changing the connection URL) is planned for the next build and is not part of this version.
- **One model per concept.** Each concept is a two-state model (not mastered, mastered) with four parameters: starting mastery, chance of learning after each answer, slip (wrong while mastered) and guess (right while not mastered).
- **Multi-concept questions.** A question tagged with several concepts updates each of them using the same answer (naive credit assignment).
- **"I'm not sure".** Treated as a wrong answer with almost no chance of a lucky guess.
- **Gap threshold.** A concept below 0.6 is a gap and 0.8 or above is strong. These are the thresholds the UI uses for words like *Needs practice*.
- **Root cause.** From the weakest concept just assessed, walk back to the weakest prerequisite that is also a gap and has been asked about, and recommend that.
- **One lesson.** The first lesson for that concept that the learner has not already tried. A failed follow-up check gives a repeat-gap recommendation with a new lesson.
- **Fitting.** Parameters are fitted per concept by expectation maximisation (EM) with sensible bounds. Tests check that EM recovers known parameters from generated data.

| Endpoint | Purpose |
|---|---|
| `POST /v1/onboarding` | Seed a new learner from experience and the placement quiz, return the start module |
| `POST /v1/quiz-result` | Update the model from a quick check and return the recommendation |
| `POST /v1/got-it` | Apply a learning step after "Got it!" |
| `GET /v1/concepts`, `GET /health` | Concept graph and lessons, service status |

## 4. Initial implementation

- **Engine service:** Python and FastAPI, in `backend/circuit_coach/`. It is a port of the engine already running in the prototype, so behaviour matches (`tests/test_parity.py` also checks that the concept graph and lesson ids match the frontend's).
- **API contract:** every response is a typed model; the OpenAPI schema is committed and a test fails if it drifts from the code or the frontend types.
- **Prototype connection:** with `VITE_API_URL` set, the placement, quiz-result and "Got it!" steps go to the service, and the top bar shows "Engine: API". If the service is unreachable, returns an error or takes longer than 4 seconds, the prototype falls back to its in-browser engine and says so.
- **Data pipeline:** a made-up learner generator with a seeded 70:30 split by learner, saved as CSV with the hidden ground truth and checksums (`backend/datasets/`), plus a validator.
- **Tests:**
  - Backend, 86 tests: BKT formulas and EM recovery of three parameter sets, gap detection and the prerequisite walk (direct gaps, multi-level prerequisite gaps, tried lessons, repeat gaps), the API and its contract, the simulator and dataset files, and the evaluation report.
  - Frontend, 17 tests, plus 8 end-to-end tests that run when a service is available: the API-mode requests, error status, timeout, fallback and recovery, and that every demo preset lands where its label says.
  - End-to-end: the four demo scenarios (direct gap, hidden cause, clean result, failed follow-up) run through the real service and again through the browser engine, which must agree; the service is also stopped mid-journey and restarted. Results and the steps to repeat the demo are in [e2e_results.md](e2e_results.md).
- **Evaluation code:** a ladder of predictors, the diagnosis evaluation, an EdNet loader, and three analysis scripts, all reproducible from the commands in `backend/README.md`.

## 5. Evaluation design

**Evaluation criteria.** The engine is judged on two questions: does it predict a learner's next answer, and does it find the right gap and the right lesson.

**Made-up learners.** Real data from the NGOs does not exist yet, and real datasets do not say which concept a learner truly lacked. So we generate learners with a hidden mastered or not-mastered state per concept. The assumptions are written at the top of `simulate.py` and in [synthetic_data.md](synthetic_data.md). In short:

- Starting mastery depends on experience and on prerequisites.
- Every answer is a chance to learn, but learning is five times slower while a prerequisite is not mastered. This is exactly what plain BKT cannot see.
- A question tagged with several concepts needs all of them.
- Learners who do not know sometimes choose "I'm not sure".

Each run has 3,000 learners, split 70% to fit and 30% to test, and we use 5 runs. A learner makes 29.3 answers on average, so one run holds about 88,000 answers (87,000 to 88,600 across the 5 runs; 88,571 for seed 0).

**Real data.** EdNet KT1 (Choi et al., 2020): real answers from a Korean English-test tutoring app, under a research licence (CC BY-NC 4.0). We used a random sample of 14,460 students with at least 30 answers (first 300 kept), split 80:20 by student, and its 189 concept tags. The full sample holds 1,765,406 answers, of which 357,756 are in the test portion that the results below are scored on. It has no prerequisite graph and no hidden truth, so it can only test **next-answer prediction**.

**Measures.** Next-answer prediction uses AUC, accuracy, log loss and RMSE. For diagnosis, at the end of each module quick check we compare the engine with the hidden truth:

- **True gap:** an assessed concept the learner has not mastered.
- **True blocker:** an unmastered concept with all prerequisites mastered. It is what must be fixed first.
- **Hidden-prerequisite case:** the real blocker is upstream of the assessed gap.

**Baselines.** Global average; each question's own accuracy; the learner's running accuracy on the tagged concepts; BKT with hand-set parameters; BKT with fitted parameters. For diagnosis, the status quo is "study the concept you got wrong". The full set of metrics and how to reproduce the results is in [evaluation.md](evaluation.md).

## 6. Baseline results

### 6.1 Made-up learners: predicting the next answer

| Method | AUC | Accuracy | Log loss | RMSE |
|---|---|---|---|---|
| Global average | 0.500 | 0.652 | 0.648 | 0.477 |
| Per-question accuracy | 0.603 | 0.665 | 0.628 | 0.468 |
| Learner's running accuracy | 0.613 | 0.681 | 0.631 | 0.467 |
| BKT, hand-set parameters | 0.649 | 0.713 | 0.598 | 0.452 |
| **BKT, fitted** | **0.688** | 0.701 | **0.595** | **0.450** |

Run-to-run spread is at most 0.01. BKT is the best predictor, and fitting parameters raises AUC by 0.04. Accuracy is slightly lower, so we treat the two BKT versions as close.

### 6.2 Made-up learners: finding the gap and the lesson (fitted parameters)

| Method | Gap F1 | Recommendation is a true blocker | Hidden-prerequisite cases solved | Missed gaps | False alarms |
|---|---|---|---|---|---|
| Study what you got wrong | 87.0% | 31.2% | 7.4% | 1.0% | 50.0% |
| BKT, assessed concept only | 89.1% | 28.5% | 5.0% | 2.6% | 31.9% |
| **BKT + prerequisite walk** | **89.1%** | **59.2%** | **61.9%** | 2.6% | 31.9% |

- BKT finds gaps slightly better than the status quo and cuts false alarms (a lesson recommended when the learner has no gap) from 50% to 32%.
- **The prerequisite walk is what finds hidden causes.** Without it, the engine almost never recommends the real blocker (5.0% of hidden cases); with it, 61.9%.
- Mastery estimates match the hidden truth with AUC 0.85.

### 6.3 Real data: EdNet (357,756 test answers)

| Method | AUC | Accuracy | Log loss | RMSE |
|---|---|---|---|---|
| Global average | 0.500 | 0.619 | 0.665 | 0.486 |
| **Per-question accuracy** | **0.721** | **0.688** | **0.590** | **0.450** |
| Learner's running accuracy | 0.598 | 0.615 | 0.657 | 0.482 |
| BKT, hand-set parameters | 0.570 | 0.517 | 0.767 | 0.530 |
| BKT, fitted, all tags | 0.627 | 0.625 | 0.645 | 0.476 |
| BKT, fitted, first tag only | 0.641 | 0.647 | 0.633 | 0.470 |

Fitted BKT beats the learner's own running accuracy and the hand-set version, but **loses clearly to simple per-question accuracy.**

## 7. What worked and what did not

**Worked**

- Standard BKT is a sound baseline. It beats simple baselines on made-up learners, and fitting helps on both datasets.
- The prerequisite walk turns a model that almost never finds hidden causes into one that does so about 62% of the time.
- The service matches the prototype's behaviour, and the prototype degrades safely when it is down: the full journey was run with the service stopped mid-way and restarted.
- The system is testable end to end: the contract, the engine rules, the dataset files, the report and the learner journey all have automated tests.

**Did not work, with evidence**

1. **Multi-concept questions distort the model.**
   - Fitting on all tagged answers puts the mean slip at 0.25. Fitting on single-concept questions only gives 0.14, against a true value near 0.09. Five of ten concepts hit the 0.30 limit, against one of ten.
   - On EdNet, using only the first tag beats using all tags (AUC 0.641 against 0.627).
   - In the made-up data, **31.6% of hidden-prerequisite misses recommend a concept the learner actually knew.** A wrong answer on a two-concept question blames both.
2. **BKT ignores question difficulty.** On real data it trails per-question accuracy by 0.08 AUC, because real questions differ a lot in difficulty.
3. **Too many false alarms.** About 32% of checks with no true gap still trigger a lesson, because one or two answers per concept is little evidence.
4. **BKT does not know prerequisites in the model itself.** The walk is a rule added afterwards. It cannot use the fact that learning is slower while a prerequisite is missing.

| Failure analysis: hidden-prerequisite cases | Share |
|---|---|
| Found the true blocker | 60.5% |
| Recommended a concept the learner actually knew | 31.6% |
| The true blocker was asked about but looked fine | 4.1% |
| Recommended a real gap, but the real blocker was further upstream | 2.5% |
| Engine saw no gap at all | 1.3% |

Neither dataset shows that learners learn more. That needs real learners.

## 8. POC v0.1 foundations

**Checkpoint: a first working technical POC exists.** It runs end to end and can be repeated by anyone from the repository.

| Part | State |
|---|---|
| Learner app and trainer console (clickable prototype, English and Hindi, deployed) | Working |
| Engine service: onboarding, quiz result with one recommendation, "Got it!", repeat-gap check | Working, 86 backend tests |
| Prototype connected to the service, with fallback to the in-browser engine | Working, tested including service failure and recovery |
| Made-up learner data with hidden truth, saved and validated | Working |
| Baseline evaluation on made-up and real data, failure analysis | Working, reproducible, reports in `backend/results/` |
| Architecture and API contract | Committed (`backend/docs/`) |
| Server-side storage of learners | Not built (planned) |
| Demo video | Not recorded yet (steps in [e2e_results.md](e2e_results.md)) |

The Hackathon 1 issues are all covered:

| Issue | Covered by |
|---|---|
| T1 Architecture and API contracts | `architecture.md`, `api_contract.md`, `openapi.json`, `tests/test_contract.py` |
| T2 BKT | `bkt.md`, `tests/test_bkt.py` |
| T3 Prerequisite diagnosis and recommendations | `diagnosis.md`, `tests/test_diagnosis.py` |
| T4 React and FastAPI integration | `engineClient.ts`, `src/api/__tests__/engineClient.test.ts` |
| T5 Synthetic learner generator | `synthetic_data.md`, `dataset.py`, `datasets/` |
| T6 Evaluation and baselines | `evaluation.md`, `tests/test_evaluation.py`, `results/` |
| T7 End-to-end test and demo | `e2e_results.md`, `src/api/__tests__/journey.e2e.test.ts` |

To run it: start the service (`uvicorn circuit_coach.api:app --port 8000` in `backend/`), set `VITE_API_URL=http://localhost:8000` in `frontend/.env.local` and run `npm run dev` in `frontend/`. The top bar then shows "Engine: API".

## 9. Preparing the component for the focused Hack 1 build

The failures in section 7 set the next steps. Each is measured against the baseline in section 6.

| Candidate improvement | Targets | How we will know |
|---|---|---|
| Credit only the first concept tag, or split credit across tags | Multi-concept distortion (slip 0.25 against 0.09 true) | Fitted slip near the true value; fewer recommendations of concepts the learner knew (31.6% now) |
| Add question difficulty to the model | The 0.08 AUC gap to per-question accuracy on EdNet | AUC on EdNet at or above per-question accuracy (0.721) |
| Make the model prerequisite-aware | The walk being a rule outside the model | Higher share of hidden-prerequisite blockers found (61.9% now) |
| Require more evidence before a lesson | False alarms (31.9%) | False alarms down without raising missed gaps (2.6%) |
| Store learners on the server | Learner records only in the browser | Learner state survives a browser change; contract tests still pass |

## 10. Corrections to the submitted document

| Submitted | Corrected here |
|---|---|
| Learner state is stored in PostgreSQL | The service is stateless and learner records are kept in the browser. Server-side storage is planned (SQLite first, PostgreSQL by changing the connection URL) and is not built |
| About 36 answers per learner | The mean is 29.3 across the 5 runs (29.5 for seed 0), so one run of 3,000 learners holds about 88,000 answers |
| 357,756 EdNet answers | That is only the test portion. The full sample is 1,765,406 answers from 14,460 students |

Other updates: the test counts (86 backend, 17 frontend and 8 end-to-end, up from 29), the RMSE column, the committed datasets and the API contract.
