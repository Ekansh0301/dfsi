# dsi-monsoon-2026-03b
Identifying what a learner needs next: How might we infer a learner’s current understanding and recommend what they should learn, practise or revisit next?

## Circuit Coach

An adaptive micro-remediation layer for vocational learners. After every quick check it diagnoses the one concept that broke down, prescribes one short fix, and routes unresolved confusion to a trainer.
Anchor NGOs: Barabari Collective, Nirmaan.

This repository holds the **UI prototype** (`frontend/`) and the **knowledge-tracing engine** (`backend/`). By default the prototype runs the engine in the browser; set `VITE_API_URL` to send the model steps to the backend service instead.

| Path | What |
|---|---|
| [`frontend/`](frontend) | Clickable prototype (React + TypeScript + Vite): learner app, trainer console, side-by-side demo, flow map |
| [`backend/`](backend) | Engine service (Python, FastAPI): Bayesian Knowledge Tracing baseline, made-up learner generator, evaluation on made-up and real (EdNet) data |

## Results at a glance

![Baseline against the improved model on 3,000 simulated learners per run, Barabari's quiz format](backend/results/model_comparison.png)

The service now answers with the improved model by default. On simulated learners in Barabari's quiz format (hidden mastery known, 5 runs of 3,000 learners each), it finds the real root cause of a gap 58% of the time (baseline 49%), sends 27% of learners to a concept they already knew (baseline 42%) and raises 31% false alarms (baseline 38%). Compared run by run, it is clearly better on 12 of 14 measures and not clearly different on the other two (missed gaps), see [`paired_comparison.md`](backend/results/paired_comparison.md).

With the same prerequisite walk, knowledge tracing finds 12 to 24 points more true blockers than plain accuracy ([`accuracy_baseline.md`](backend/results/accuracy_baseline.md)). The walk is what lifts both well above "study what you got wrong", which finds the hidden cause in under 8% of cases. On real student answers (EdNet, next-answer prediction), the improved model reaches AUC 0.729 against 0.627 for the baseline.

![Calibration of the predicted chance of a right answer and of the mastery estimate](backend/results/calibration.png)

The predicted chance of a right answer is well calibrated. The mastery estimate runs about 10 points high between 0.2 and 0.7, so the trainer console shows bands (Needs work, Getting there, Strong) instead of percentages. Details in [`calibration.md`](backend/results/calibration.md).

What these results do not show: they come from simulated learners and from EdNet (next-answer prediction only), not from learners at Barabari or Nirmaan, and nothing here shows that learners learn more. Full evidence, limits and the promotion decision: [technical design document](backend/docs/Technical_Design_Doc.md).

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and use **Demo scenarios** in the top bar to jump to any point in the story.

To run the knowledge-tracing steps on the engine service instead of in the browser, start it in a second terminal and point the prototype at it:

```bash
cd backend
pip install -e ".[eval,dev]"
python -m uvicorn circuit_coach.api:app --port 8000
```

Then set `VITE_API_URL=http://localhost:8000` in `frontend/.env.local` and restart `npm run dev`; the top bar shows **Engine: API**.

## Run with Docker

```bash
docker compose up --build
```

This builds and starts both parts: the prototype at http://localhost:8080, already connected to the engine service at http://localhost:8000 (API docs at `/docs`). Learner state is kept in SQLite on a Docker volume. Each part also builds on its own: `docker build -t circuit-coach-engine backend` and `docker build -t circuit-coach-app --build-arg VITE_API_URL=http://localhost:8000 frontend`.

## Tests

`cd backend && pytest` for the engine, `cd frontend && npm test && npm run typecheck && npm run build` for the prototype. GitHub Actions runs both, the end-to-end journey against the running service, and a Docker build and smoke test on every push (`.github/workflows/tests.yml`).

## Deploy (Vercel)

Import this repository in Vercel with:

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Routing is hash-based, so no rewrite rules are needed.
