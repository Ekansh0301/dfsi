# Circuit Coach · UI prototype

Final UI design for **DFSI 2026 Problem 3B**: adaptive micro-remediation for vocational learners.

## Run

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # static site in dist/ (relative paths, works on any static host)
npm run typecheck
npm run format
```

To use the engine service in `../backend` instead of the in-browser engine, copy `.env.example` to `.env.local` and set `VITE_API_URL`. The top bar shows which engine is answering, and the prototype falls back to the in-browser engine if the service is unreachable.

To deploy on Vercel, import the repo with Root Directory `frontend`, build command `npm run build` and output directory `dist`. Routing is hash-based, so no rewrite rules are needed.

`npm run build` first runs `npm run check:dashes`, which fails if an em dash or en dash appears in the site content or READMEs.

## What's where

| Path | Contents |
|---|---|
| `src/learner/` | Learner app screens (onboarding, quiz, results, recommendation, lesson, stuck/help, progress, messages) |
| `src/educator/` | Trainer console (triage queue, learner detail & resolution, resolved log) |
| `src/shell/` | Prototype-only shell: overview, phone frame + design notes, side-by-side demo, flow map, demo scenarios |
| `src/api/types.ts` | Data contract (Design Doc §5 shapes) shared with the future backend |
| `src/api/mockServer.ts` | In-browser mock backend (localStorage). One function per planned endpoint |
| `src/engine/engine.ts` | Stand-in knowledge-tracing engine: BKT, root-cause search, single recommendation |
| `src/data/` | Demo curriculum (concept DAG, modules, bilingual questions), remedial content, fictional seed data |
| `src/components/` | Circuit `Figure` (SVG, highlightable parts) and trainer `ConceptMap` |
| `src/lib/` | Store hook, i18n (English/Hindi) |
| `src/styles/` | Design tokens (light/dark) and component styles |

## Prototype conventions

- **Shared state:** the learner app and trainer console share one simulated backend, persisted in `localStorage`. Changes sync across tabs and across the side-by-side iframes.
- **Demo scenarios:** the menu in the top bar resets the data to a specific moment of the story. "Reset all demo data" starts over.
- **Embed mode:** `?embed=1#/learner` or `?embed=1#/educator` renders an app without the prototype shell.
- **Swapping in the real backend:** replace the bodies of the exported functions in `mockServer.ts` with `fetch` calls. Screens don't change.
