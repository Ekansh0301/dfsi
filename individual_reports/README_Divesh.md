# Individual report: Divesh

**Course:** DFSI 2026, Problem 3B (identifying what a learner needs next) | **Team:** Impact Theory | **Project:** Circuit Coach, Hackathon 2

## My contribution: audio (the listen button)

After Hackathon 1, the instructors asked for voice support, because many learners read slowly or prefer Hindi. My part was a listen button that reads the app aloud.

- **What it reads.** A speaker icon on each question reads the question and its choices ("A ... B ... C ..."), on each lesson step reads the step (and the answer once shown), and on the recommendation reads the diagnosis and the lesson offered. Tapping again stops it.
- **Hindi and English.** It follows the learner's language and uses the matching voice (`hi-IN` or `en-IN`), preferring a natural or online voice when the device has one, at a slightly slower pace for clarity.
- **No outside service.** It uses the browser's own speech (`speechSynthesis`), so there are no audio files to generate or license, nothing is sent anywhere, and it keeps working offline.
- **Fails gracefully.** If the device has no voice for the learner's language, the button hides instead of showing something broken.
- **Tests.** `frontend/src/components/__tests__/listen.test.ts` checks that an Indian voice is preferred, that a natural voice wins among several, and that the button hides when no voice matches.

## Alongside it

I also built the results presentation for the repository: the figures in `backend/results/` (the improved-model comparison, run-by-run differences, tracing against plain accuracy, EdNet, robustness, the hardest cases and what the tests protect), the script that draws them from the saved results, and a written reading with a caveat for each in `backend/results/overview.md`. The README shows the key ones at the top.

## Hackathon experience

Audio taught me how much of a feature is the edge cases. Voices load a moment after the page does, laptops often have no Hindi voice, and speech must stop when the learner moves on. Most of the work was making it quiet and reliable when something is missing. For the figures, the lesson was to check every chart by eye: our first versions had legends covering labels and axes that exaggerated small differences, and fixing them made the results more honest.

## Key learnings

- **Accessibility is a design constraint.** Learners with low literacy or in a hurry benefit from hearing the question, so audio belongs on the main path.
- **Prefer simple, dependable options.** Browser speech is less polished than recorded human audio, but it works everywhere without cost. Recorded natural audio is the clear next step and can replace it without changing the button.
- **Degrade, do not break.** A feature that hides itself when it cannot work is better than one that errors.
- **A chart is an argument.** Starting bars at zero, showing ranges, and writing the caveat next to the figure keeps the evidence trustworthy.

## Where to look

`frontend/src/components/ListenButton.tsx` | `frontend/src/learner/Quiz.tsx`, `Remedial.tsx`, `Loop.tsx` (where it appears) | `backend/scripts/plot_results.py` | `backend/results/overview.md`
