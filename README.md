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
