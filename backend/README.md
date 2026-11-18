# Circuit Coach engine (backend)

Knowledge tracing and recommendation service for Problem 3B. Given a learner's answers, it estimates how well they know each concept, finds the concept that is really holding them back, and picks one lesson. It is the same logic the prototype runs in the browser, as a Python service with a baseline evaluation.

**Status (POC v1.0):** two models. The baseline (standard Bayesian Knowledge Tracing per concept, parameters fitted from data, plus a walk back through prerequisites) stays selectable; the improved model (first-tag credit, question difficulty, prerequisite-aware learning, more evidence before a lesson) is the default, as decided in Hackathon 2 after the real-data check. The model is frozen since tag `v0.9`.

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
| `circuit_coach/barabari.py` | Reads Barabari's quiz format and turns attempts into engine events |
| `circuit_coach/storage.py` | Optional learner storage (SQLite or PostgreSQL via `CIRCUIT_COACH_DB`) |
| `circuit_coach/dataset.py` | Save, load, split (70:30) and validate a made-up dataset |
| `circuit_coach/diagnosis_eval.py` | Does the engine find the right gap and the right lesson? |
| `circuit_coach/ednet.py` | Loader for the real EdNet dataset |
| `circuit_coach/fitted_params.json` | BKT parameters used by the service (fitted on made-up learners); the browser carries a copy |
| `circuit_coach/item_difficulty.json` | Per-question difficulty read by the improved model; the browser carries a copy |
| `scripts/` | `run_synthetic.py`, `run_ednet.py`, `compare_models.py`, `served_model_check.py`, `estimate_item_difficulty.py`, `export_parity_cases.py`, `export_openapi.py`, `generate_dataset.py` and more |
| `results/` | Evaluation output (Markdown tables and raw JSON) |
| `datasets/` | Saved made-up dataset (seed 0, 500 learners) with ground truth |
| `docs/` | Architecture, API contract (`openapi.json`) and notes per component |

## Docs

- [Demo plan](docs/demo_plan.md): the 10 minute live demo script, setup checklist and what to do if something fails
- [Test spec](docs/test_spec.md): every change since Sprint 3, its tests, its measured effect and what is still weak
- [Model comparison](results/model_comparison.md): the improved model against the baseline (`python scripts/compare_models.py`), and [paired by run](results/paired_comparison.md) with 95% intervals
- [Accuracy baseline](results/accuracy_baseline.md): BKT against plain accuracy with the same prerequisite walk
- [Evaluation at a glance](results/overview.md): nine figures with a short reading and caveat each (`python scripts/plot_results.py`)
- [Barabari's quiz format](docs/barabari_format.md): question types, partial credit, retakes, concept tags and the adapter endpoint
- [Technical design document (POC v1.0)](docs/Technical_Design_Doc.md): changes in response to feedback and review, architecture, the engine, results, robustness, calibration, POC v1.0 status
- [Architecture and data flow](docs/architecture.md)
- [API contract](docs/api_contract.md) and the generated [OpenAPI schema](docs/openapi.json)
- [Knowledge tracing (BKT)](docs/bkt.md): update rules, "I'm not sure", multi-concept questions, EM fitting and what the tests check
- [Made-up learner generator](docs/synthetic_data.md): assumptions, files, split and validation
- [End-to-end results and demo script](docs/e2e_results.md): repeat the demo, test results, API failure and fallback
- [Evaluation and baselines](docs/evaluation.md): models, metrics, how to reproduce, results
- [Diagnosis and recommendations](docs/diagnosis.md): gap threshold, prerequisite walk, lesson choice, repeat gaps

## API

| Endpoint | Purpose |
|---|---|
| `GET /health` | Status and whether fitted parameters are loaded |
| `GET /v1/concepts` | Concept graph, modules, lesson ids |
| `POST /v1/onboarding` | Seed a new learner from experience and the placement quiz |
| `POST /v1/quiz-result` | Update the model from a quick check, return one recommendation |
| `POST /v1/got-it` | Apply a learning step after "Got it!" and record the finished lesson |
| `POST /v1/marked-answer` | A trainer's mark for a short answer, as partial credit |
| `POST /v1/barabari/quiz-attempt` | One attempt in Barabari's own quiz format |
| `GET /v1/learners/{learner_id}/state` | A saved learner state (storage on) |

Settings (environment variables, all optional):

| Variable | Effect |
|---|---|
| `CIRCUIT_COACH_MODEL` | Default model, `improved` (default) or `baseline` |
| `CIRCUIT_COACH_DB` | Database URL for learner storage, for example `sqlite:///coach.db` |
| `CIRCUIT_COACH_API_KEY` | Require this value in the `X-API-Key` header on `/v1/` calls |
| `ALLOWED_ORIGINS` | Sites allowed to call the service from a browser (default: local prototype and dfsi.vercel.app) |

Requests carry the learner state (`mastery`, `observations`, `tried`) and return the updated state, so the service stores nothing unless storage is on. Request and response fields follow `frontend/src/api/types.ts`. The full schemas, with examples and error codes, are in [docs/api_contract.md](docs/api_contract.md). After changing a request or response model, run `python scripts/export_openapi.py`; `tests/test_contract.py` fails until the committed schema matches.

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
