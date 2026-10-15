# System architecture

Circuit Coach has three parts: a React app (learner app and trainer console), a stateless engine service (FastAPI), and offline evaluation scripts. This page describes each part, how data moves between them, and where each piece of the code lives. The request and response schemas are in [api_contract.md](api_contract.md).

![Architecture diagram](architecture.svg)

## 1. Components

```mermaid
flowchart LR
    subgraph Browser["Browser (frontend/)"]
        LA["Learner app<br/>onboarding, quick checks, lessons"]
        TC["Trainer console<br/>escalations, cohort gaps"]
        MS["mockServer.ts<br/>learner records in localStorage"]
        EC["engineClient.ts<br/>calls the service when VITE_API_URL is set"]
        BE["engine.ts<br/>in-browser engine (fallback)"]
        LA --> MS
        TC --> MS
        MS --> EC
        MS --> BE
    end

    subgraph Service["Engine service (backend/circuit_coach/)"]
        API["api.py<br/>FastAPI, validates requests"]
        ENG["engine.py<br/>1. trace  2. root cause  3. recommend"]
        BKT["bkt.py<br/>BKT update and EM fitting"]
        CUR["curriculum.py<br/>concept graph, modules, lesson ids"]
        P["fitted_params.json"]
        API --> ENG
        ENG --> BKT
        ENG --> CUR
        ENG --> P
    end

    subgraph Offline["Offline scripts (backend/scripts/)"]
        SIM["simulate.py<br/>made-up learners, hidden mastery"]
        ED["ednet.py<br/>real EdNet KT1 answers"]
        EV["run_synthetic.py, run_ednet.py<br/>fit, compare baselines, report"]
        SIM --> EV
        ED --> EV
    end

    EC -- "JSON over HTTP" --> API
    EV -- "writes" --> P
    EV -- "writes" --> R["results/*.md, *.json"]
```

| Component | Code | Responsibility |
|---|---|---|
| Learner app | `frontend/src/learner/` | Onboarding, module quick checks, the one recommended lesson, "Got it!" and "I'm still stuck" |
| Trainer console | `frontend/src/educator/` | Escalation queue, repeat gaps, cohort gaps, replies to learners |
| Learner store | `frontend/src/api/mockServer.ts` | Holds every learner record (answers, mastery, tried lessons, re-checks, escalations) in `localStorage` |
| Engine client | `frontend/src/api/engineClient.ts` | Sends the three model steps to the service, reports the engine mode, falls back on any failure |
| In-browser engine | `frontend/src/engine/engine.ts` | Same logic as the service, used when there is no service or it is unreachable |
| HTTP layer | `backend/circuit_coach/api.py` | Request validation, the five endpoints, CORS |
| Engine | `backend/circuit_coach/engine.py` | Tracing, root-cause walk, one recommendation, onboarding |
| BKT | `backend/circuit_coach/bkt.py` | Per-concept Bayesian Knowledge Tracing and EM fitting |
| Curriculum | `backend/circuit_coach/curriculum.py` | Concept graph, modules and lesson ids; must match `frontend/src/data/` (checked by `tests/test_parity.py`) |
| Parameters | `backend/circuit_coach/fitted_params.json` | Fitted BKT parameters loaded at start-up (hand-set values if the file is missing) |
| Simulator | `backend/circuit_coach/simulate.py` | Made-up learners with known hidden mastery |
| Evaluation | `backend/scripts/`, `backend/circuit_coach/prediction.py`, `diagnosis_eval.py` | Baselines, metrics, reports in `backend/results/` |

## 2. Where state lives

The service is **stateless**. Each request carries the learner's model state and each response returns the updated state:

| Field | Type | Meaning |
|---|---|---|
| `mastery` | concept id to number in [0.01, 0.99] | P(concept mastered) |
| `observations` | concept id to integer | Answers seen per concept |
| `tried` | concept id to list of lesson ids | Lessons the learner has already opened |

Everything else (answers, re-check schedule, escalations, messages) is kept by the frontend store. Persistence on the server (SQLite first, PostgreSQL by changing the connection URL) is planned but not built, so nothing is stored server side today.

## 3. Data flow for one learner

```mermaid
sequenceDiagram
    autonumber
    actor L as Learner
    participant UI as Learner app
    participant S as Store (mockServer.ts)
    participant API as Engine service
    L->>UI: Chooses experience, answers placement quiz
    UI->>S: finishOnboarding(experience, answers)
    S->>API: POST /v1/onboarding {experience, events}
    API-->>S: {state, start_module_id}
    S-->>UI: Start at module N
    L->>UI: Answers the module quick check
    UI->>S: submitQuiz(module, answers)
    S->>API: POST /v1/quiz-result {state, module_id, events, recheck_concept?}
    API-->>S: {state, recommendation or null}
    S-->>UI: One lesson (or "all clear")
    L->>UI: Opens the lesson, taps "Got it!"
    UI->>S: gotIt()
    S->>API: POST /v1/got-it {state, concept_id}
    API-->>S: {state}
    S->>S: Schedule a spaced re-check question
    Note over S,API: A failed re-check is sent later as recheck_concept:<br/>repeat-gap recommendation with a new lesson, and the trainer is flagged
```

If any call fails (network error, non-2xx status, or no answer in 4 seconds) `engineClient.ts` returns `null`, the store runs the same step with the in-browser engine, and the top bar switches to "Engine: API unreachable, using browser". The learner flow never stops.

## 4. Engine steps

1. **Trace.** For every answer, update P(mastered) for each concept the question is tagged with (standard BKT, one model per concept). "I'm not sure" is treated as a wrong answer with almost no chance of a lucky guess (`UNSURE_GUESS = 0.02`).
2. **Root cause.** Among the concepts the quick check assessed, take the most advanced one below the gap threshold (0.6). Walk back through its prerequisites to the weakest one that has been observed and is also below 0.6, and repeat until no weak prerequisite remains.
3. **Recommend.** Return the first lesson for the root-cause concept that the learner has not tried. A failed re-check gives a repeat-gap recommendation that uses a different lesson.

Details and tests: [bkt.md](bkt.md) and [diagnosis.md](diagnosis.md).

## 5. Deployment

| Piece | How it runs |
|---|---|
| Frontend | Static build (`npm run build`), deployed on Vercel with root directory `frontend` |
| Service | `uvicorn circuit_coach.api:app --port 8000`; `ALLOWED_ORIGINS` sets CORS (comma separated, default `*`) |
| Connection | `VITE_API_URL` in `frontend/.env.local`; unset means the in-browser engine only |
