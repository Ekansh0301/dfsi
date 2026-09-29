# dsi-monsoon-2026-03b
Identifying what a learner needs next: How might we infer a learner’s current understanding and recommend what they should learn, practise or revisit next?

## Circuit Coach

An adaptive micro-remediation layer for vocational learners. After every quick check it diagnoses the one concept that broke down, prescribes one short fix, and routes unresolved confusion to a trainer.
Anchor NGOs: Barabari Collective, Nirmaan.

This repository currently holds the **UI prototype** (`frontend/`). The knowledge-tracing engine runs in the browser behind a mock API with the same request and response shapes the backend service will implement.

| Path | What |
|---|---|
| [`frontend/`](frontend) | Clickable prototype (React + TypeScript + Vite): learner app, trainer console, side-by-side demo, flow map |

## Run locally

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and use **Demo scenarios** in the top bar to jump to any point in the story.

## Deploy (Vercel)

Import this repository in Vercel with:

| Setting | Value |
|---|---|
| Root Directory | `frontend` |
| Framework Preset | Vite |
| Build Command | `npm run build` |
| Output Directory | `dist` |

Routing is hash-based, so no rewrite rules are needed.
