# Demo plan (Hackathon 2 and the formal demo)

A 10 minute live demo of POC v0.9 with the real engine service, plus a fallback if anything fails. The two Module 3 answer sets, the true/false question, the short-answer marking flow and the fallback were each checked against the running service; rehearse the whole script once before the demo.

## Setup (15 minutes before)

Terminal 1, the engine service (keep it visible: its log shows each request):

```bash
cd backend
python -m uvicorn circuit_coach.api:app --port 8000
```

Terminal 2, the prototype connected to it:

```powershell
cd frontend
$env:VITE_API_URL = "http://localhost:8000"
npm run dev
```

Checklist:

- [ ] http://localhost:5173 shows **Engine: API** in the top bar.
- [ ] http://localhost:8000/docs opens (the API page).
- [ ] Demo scenarios, then **Reset all demo data**.
- [ ] Optional: to show the improved model, also set `$env:VITE_ENGINE_MODEL = "improved"` before `npm run dev`; the top bar then says **Engine: API (improved)**.

Quiz options are shuffled, so pick answers by their text, never by letter.

## Script

| Time | Step | Do | Say |
|---|---|---|---|
| 0:00 | Problem | Overview page | Learners at Barabari and Nirmaan study in short phone sessions; misunderstandings surface late and trainers cannot see who is stuck. |
| 0:45 | The engine is real | Open `/docs` on port 8000 | Every recommendation comes from this Python service: Bayesian Knowledge Tracing plus a prerequisite walk. |
| 1:15 | Direct gap | Demo scenarios, "Onboarded, starting Module 3", Start quick check. Answer: "A switch", "Phase (live) wire", "On: the battery is connected", "L2 only", "Green (or green-yellow)" | Recommends **Reading circuit diagrams**. Point at Terminal 1: `POST /v1/quiz-result 200`. |
| 2:30 | Hidden cause | Reset, "Onboarded, starting Module 3" again. Answer: "A lamp", "Phase (live) wire", "On: the battery is connected", "L2 only", "Green (or green-yellow)" | Recommends **The 4 symbols you need**: stuck on diagrams because symbols are weak. "Why this?" shows the chain. |
| 3:45 | Barabari's format | Learner app, Module 1 quick check: the last question is true/false (5 points); results show points | Barabari's quizzes use multiple choice, true/false and short answers with points; the engine counts a true/false answer as weaker evidence. |
| 4:30 | Short answer and trainer marking | Module 2 quick check: type an answer to the last question. Results say it is with the trainer. Trainer console, **To mark**: give 1/4 with a note, Save | The trainer's mark becomes partial credit (`POST /v1/marked-answer`); the learner gets the mark in Messages and, here, a lesson on Ohm's law. |
| 6:00 | Escalation | Demo scenarios, "Learner escalated to trainer", Trainer console | Repeat gaps come first; the case shows what the app saw, what was tried, and the learner's words. |
| 7:00 | Fallback | Stop Terminal 1 (Ctrl+C), finish any quick check | Top bar: "API unreachable, using browser". The learner is never blocked. Restart the service: the next step shows "Engine: API" again. |
| 8:00 | Results | `backend/results/model_comparison.md` | Improved model: hidden blockers found 49.0% to 58.3%, false alarms 38.2% to 30.7% on Barabari-style learners; next-answer AUC 0.672 to 0.701. |
| 9:00 | Honest limits | | Made-up learners and EdNet only; no NGO learner data yet; mastery estimates run about 10 points high in the middle range (calibration). |

## If something fails

| Problem | Fix |
|---|---|
| Top bar says "Engine: in browser" | `VITE_API_URL` was not set: stop the site, set it, restart `npm run dev` |
| Port 8000 busy | Start the service on another port and set `VITE_API_URL` to match |
| The service crashes mid-demo | Carry on: the browser engine takes over (that is the fallback step) |
| No network or laptop problem | Use https://dfsi.vercel.app/ (browser engine only) and the presets in Demo scenarios |
| Everything else | Play the recorded demo video |

## Roles

- One person drives the laptop; one narrates; one watches Terminal 1 and answers technical questions.
- Practise the script twice with a timer; it should take 9 to 10 minutes.
