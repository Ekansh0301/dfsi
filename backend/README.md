# Circuit Coach engine (backend)

Knowledge tracing and recommendation service for Problem 3B. Given a learner's answers, it estimates how well they know each concept, finds the concept that is really holding them back, and picks one lesson. It is the same logic the prototype runs in the browser, as a Python service with a baseline evaluation.

**Status (Sprint 2):** baseline only. Standard Bayesian Knowledge Tracing (BKT) per concept, with parameters fitted from data, plus a simple walk back through prerequisites. The prerequisite-aware model is planned for Sprint 3.

## Run

```bash
cd backend
uv venv .venv && source .venv/bin/activate
uv pip install -e ".[eval,dev]"

pytest                                         # unit tests
uvicorn circuit_coach.api:app --port 8000      # the service, docs at /docs
```

To use the service from the prototype, set `VITE_API_URL=http://localhost:8000` in `frontend/.env.local` and run `npm run dev` in `frontend/`. The top bar then shows "Engine: API". If a call fails, the prototype falls back to its in-browser engine.

## Layout

| Path | What |
|---|---|
| `circuit_coach/curriculum.py` | Concept graph, modules and lesson ids (kept in step with the frontend by `tests/test_parity.py`) |
| `circuit_coach/bkt.py` | BKT update rules and EM fitting |
| `circuit_coach/engine.py` | Tracing, root-cause walk, one recommendation, onboarding |
| `circuit_coach/api.py` | FastAPI service (stateless: the caller sends the learner state) |
| `circuit_coach/prediction.py` | Next-answer prediction: BKT against simple baselines |
| `circuit_coach/simulate.py` | Made-up learners with hidden mastery |
| `circuit_coach/diagnosis_eval.py` | Does the engine find the right gap and the right lesson? |
| `circuit_coach/ednet.py` | Loader for the real EdNet dataset |
| `circuit_coach/fitted_params.json` | BKT parameters used by the service (fitted on made-up learners) |
| `scripts/` | `run_synthetic.py`, `run_ednet.py`, `ablation_multitag.py` |
| `results/` | Evaluation output (Markdown tables and raw JSON) |

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Status and whether fitted parameters are loaded |
| `GET /v1/concepts` | Concept graph, modules, lesson ids |
| `POST /v1/onboarding` | Seed a new learner from experience and the placement quiz |
| `POST /v1/quiz-result` | Update the model from a quick check, return one recommendation |
| `POST /v1/got-it` | Apply a learning step after "Got it!" |

Requests carry the learner state (`mastery`, `observations`, `tried`) and return the updated state, so the service stores nothing. Request and response fields follow `frontend/src/api/types.ts`.

## Reproduce the evaluation

```bash
python scripts/run_synthetic.py --learners 3000 --seeds 5   # made-up learners, about a minute
python scripts/ablation_multitag.py                          # why fitted slip rates look too high
```

The real-data check uses EdNet KT1 (about 1.2 GB) and the EdNet question file. Both come from the dataset's own page, https://github.com/riiid/ednet, which links `bit.ly/ednet_kt1` and `bit.ly/ednet-content`. EdNet is released for research under CC BY-NC 4.0. Put `ednet_kt1.zip` and the unpacked `contents/` folder in `backend/data/raw/` (not committed), then:

```bash
python scripts/run_ednet.py --users 40000
```

## What the evaluation does and does not show

- Made-up learners can test whether the engine finds a learner's real gap and root cause, because their hidden mastery is known. They only reflect the simulator's assumptions, which are written at the top of `simulate.py`.
- EdNet is real, but it has no prerequisite graph and no hidden truth, so it only checks next-answer prediction. It is a Korean English-test tutor, so it says nothing direct about electrician learners in India.
- Neither shows that learners learn more. That needs real learners.
