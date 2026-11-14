
# Handoff notes

For teammates continuing **Circuit Coach** (Team Impact Theory, DFSI 2026, Problem 3B: identifying what a learner needs next). Anchor NGOs: Barabari Collective and Nirmaan.

Live prototype: https://dfsi.vercel.app/

## 1. What exists today (POC v1.0)

| Part | Where | State |
|---|---|---|
| Clickable prototype (learner app, trainer console, side-by-side demo, flow map, English and Hindi, light and dark) with true/false and short-answer questions, points, trainer marking, a listen button, offline use and saved quiz progress | `frontend/` | Done |
| Engine service (FastAPI, Bayesian Knowledge Tracing, prerequisite walk, one-lesson recommender; two models, baseline and improved; Barabari adapter; optional SQLite or PostgreSQL storage; optional API key and size limits) | `backend/circuit_coach/` | Done, 216 tests pass |
| Made-up learner generator with hidden mastery, in two formats (Sprint 2 and Barabari's quiz format) | `backend/circuit_coach/simulate.py` | Done |
| Evaluation: model comparison (also paired by run), accuracy baseline, robustness, calibration, failure analysis, EdNet loader | `backend/scripts/`, results in `backend/results/` | Done, including the EdNet comparison for the improved model |
| Prototype connected to the engine, with fallback to the in-browser engine | `frontend/src/api/engineClient.ts`, `mockServer.ts` | Done, tested, health check on start-up |
| Docker images and compose file; GitHub Actions workflow | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`, `.github/workflows/tests.yml` | Written; the workflow has not run yet (see section 7) |
| Technical design document (final, POC v1.0) | `backend/docs/Technical_Design_Doc.md` | Done |

Read `backend/docs/Technical_Design_Doc.md` first. It explains the design, the evaluation and the results. Earlier versions are in `backend/docs/archive/`.

## 2. Run it

Everything at once with Docker:

```bash
docker compose up --build        # prototype at http://localhost:8080, engine at http://localhost:8000/docs
```

Engine service on its own:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[eval,dev]"
uvicorn circuit_coach.api:app --port 8000
pytest
```

Prototype:

```bash
cd frontend
npm install
npm run dev
```

By default the prototype uses its own in-browser engine. To use the service, copy `frontend/.env.example` to `frontend/.env.local` and set `VITE_API_URL=http://localhost:8000`. The top bar then shows "Engine: API" once the service answers, and says so and falls back to the browser engine if it does not. The top bar also shows the build version and commit.

Settings of the service (all optional): `CIRCUIT_COACH_MODEL`, `CIRCUIT_COACH_DB`, `CIRCUIT_COACH_API_KEY`, `ALLOWED_ORIGINS` (table in `backend/README.md`).

Evaluation commands are in `backend/README.md` and `backend/docs/evaluation.md`. The EdNet raw files (1.2 GB) are not in the repo. Download KT1 from https://github.com/riiid/ednet into `backend/data/raw` (the exact files and the command are in `backend/README.md`).

Test counts at the last check: 216 backend tests; 42 frontend tests plus 8 end-to-end tests that need the service running (`E2E_API_URL=http://localhost:8000 npm run test:e2e`). `npm test` works with or without a `frontend/.env.local`.

## 3. Key results

Details and tables are in the technical design document; every figure comes from a script in `backend/scripts/` that anyone can rerun.

- **Improved model against the baseline** (5 runs of 3,000 made-up learners, paired by run): clearly better on 12 of 14 measures, not clearly different on missed gaps. On learners in Barabari's quiz format it finds the hidden root cause 58.3% of the time (baseline 49.0%) and cuts false alarms from 38.2% to 30.7%. On the Sprint 2 simulator it misses more gaps in 4 of 5 runs (median +1.5 points). `results/paired_comparison.md`.
- **Does BKT earn its place?** With the same prerequisite walk, BKT finds 12 to 24 points more true blockers than plain accuracy. `results/accuracy_baseline.md`.
- **Real data (EdNet, Sprint 2 result):** per-question accuracy AUC 0.721 beats fitted BKT 0.627, because BKT ignores question difficulty.
- **Calibration:** next-answer probabilities are well calibrated; mastery estimates run about 10 points high in the middle range, so trainers see bands, not percentages.
- **EdNet, improved model:** next-answer AUC 0.729 against 0.627 for the baseline and 0.721 for per-question accuracy (`results/model_comparison.md`).
- **Promotion:** the baseline stays the service default in this release. The improved model is selectable (`?model=improved`, `CIRCUIT_COACH_MODEL`, `VITE_ENGINE_MODEL`). The EdNet condition is met; the open point is missed gaps (slightly more in some runs). We recommend promoting it; that is a team decision.

## 4. How we got here

**Hackathon 1 issues (T1 to T7)** were completed by Aman Srivastava on 14 October 2026, one commit per issue, each documented in `backend/docs/` with tests alongside:

| Issue | Covered by |
|---|---|
| T1 Architecture and API contracts | `backend/docs/architecture.md`, `api_contract.md`, `openapi.json`, `tests/test_contract.py` |
| T2 BKT | `backend/docs/bkt.md`, `tests/test_bkt.py` |
| T3 Prerequisite diagnosis and recommendations | `backend/docs/diagnosis.md`, `tests/test_diagnosis.py` |
| T4 React and FastAPI integration | `frontend/src/api/__tests__/engineClient.test.ts` |
| T5 Made-up learner generator | `backend/docs/synthetic_data.md`, `circuit_coach/dataset.py`, `backend/datasets/synthetic_seed0/` |
| T6 Evaluation and baselines | `backend/docs/evaluation.md`, `tests/test_evaluation.py`, `backend/results/` |
| T7 End-to-end test and demo | `backend/docs/e2e_results.md`, `frontend/src/api/__tests__/journey.e2e.test.ts` |

**Sprint 3** applied Barabari's quiz format (true/false, short answers with trainer marking, points, retakes, an importer and an adapter endpoint), the improved model and storage. **Sprint 4** added edge cases, robustness, calibration, the failure analysis and the revised design document, and froze the model (tag `v0.9`). **Hackathon 2** fixed the issues found in a full project review, added the listen button, offline use, Docker and the paired and accuracy comparisons, and produced POC v1.0. The detailed plan and status are in `PLAN.md`; what each change was tested with is in `backend/docs/test_spec.md`.

## 5. Open

- **Demo video:** not recorded. Steps are in `backend/docs/demo_plan.md`.
- **Decision:** make the improved model the service default or not (`backend/docs/evaluation.md`).
- **Live site:** redeploy after every merge; the top bar shows which build is running.
- **Voice:** the listen button uses the voices installed on the device. Pre-recorded natural English and Hindi audio is the next step.
- **Nirmaan:** we have no format or data from them yet. **Barabari:** their real attempt records (columns) would replace our assumed shape (`backend/docs/barabari_format.md`).
- **Mastery numbers** run about 10 points high in the middle range; a recalibration step is future work.
- **Escalations** are stored in the browser, not in the service.

## 6. Demo scenarios (verified against the engine)

1. Direct gap: symbols and wiring right, both diagram questions wrong. Recommends the circuit diagrams lesson.
2. Hidden cause: the symbol question is also wrong. Recommends the circuit symbols lesson instead.
3. Clean result: all correct. No recommendation.
4. Follow-up check failed after "Got it!": repeat-gap recommendation with a different lesson, and the trainer is flagged.
5. Barabari's format: "Module 1 check (true/false)" and "Module 2 check (short answer)", then marking in the trainer console.

Use **Demo scenarios** in the top bar, then **Reset all demo data**. The full script is `backend/docs/demo_plan.md`.

## 7. Conventions and things to know

- No em dashes or en dashes anywhere in the site content, READMEs or docs. `npm run build` runs `npm run check:dashes` and fails if one appears.
- Commits are made under your own name with a short plain message. Course PDFs and sprint documents are not committed (see `.gitignore`); the archived Sprint 2 design document in `backend/docs/archive/` is the exception.
- The curriculum lives in two places that must match: `frontend/src/data/curriculum.ts` and `backend/circuit_coach/curriculum.py`. `backend/tests/test_parity.py` checks this.
- The model parameters the service ships with (`backend/circuit_coach/fitted_params.json`) are frozen. Evaluation scripts write their fits to `backend/results/` and change the shipped file only with `--write-service-params`; `tests/test_shipped_params.py` fails if it drifts.
- Deploy: import the repository in Vercel with Root Directory `frontend`, build command `npm run build`, output directory `dist`.
- The personal repository `Ekansh0301/dfsi` (where the live site is deployed from) has its own history, without the course template's first commit. Do not merge the two repositories or push one to the other; copy changes across (for example with `git cherry-pick`) instead.
- GitHub Actions did not run on the personal repository: GitHub reported that the account is locked because of a billing issue. Fix that in the account's billing settings; the workflow itself is untested on GitHub until then. Run the checks locally with the commands in `README.md`.

## 8. Not in the repo

The original course PDFs, the UI design plan, the project summary and the Hackathon 1 plan are kept locally by Ekansh. The Hackathon 1 plan uses a different task numbering (T1 to T16) from the submitted T1 to T7, so do not reuse it as is.
