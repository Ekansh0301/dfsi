import type { Preset } from "../api/mockServer";

export type ScreenKey =
  | "welcome"
  | "track"
  | "experience"
  | "placement"
  | "start"
  | "home"
  | "quiz"
  | "results"
  | "next"
  | "learn"
  | "gotit"
  | "stuck"
  | "helpsent"
  | "progress"
  | "messages"
  | "e-queue"
  | "e-case"
  | "e-resolved";

export type Flow = "learner" | "educator" | "onboarding" | "recheck";

export interface Annotation {
  code: string;
  name: string;
  flow: Flow;
  /** UX Breakdown stage (Sprint 0 framework). */
  stage: string;
  why: string;
  /** What the system does behind this screen. */
  system?: string;
  /** Planned API call. */
  api?: string;
  route: string;
  preset?: Preset;
}

export const FLOW_LABEL: Record<Flow, string> = {
  learner: "Learner journey",
  educator: "Educator escalation",
  onboarding: "Cold-start onboarding",
  recheck: "Spaced re-assessment",
};

export const ANNOTATIONS: Record<ScreenKey, Annotation> = {
  welcome: {
    code: "O1",
    name: "Welcome & language",
    flow: "onboarding",
    stage: "Cold start",
    why: "Language comes first, before any reading-heavy content. Both options are written in their own script, so a learner can find theirs without reading English. The app promise fits in one sentence.",
    route: "/learner/welcome",
    preset: "fresh",
  },
  track: {
    code: "O2",
    name: "Track selection",
    flow: "onboarding",
    stage: "Cold start",
    why: "There is no performance history yet, so we ask instead of guessing. Other trades are shown but disabled, which signals the product core is reusable across vocational tracks.",
    route: "/learner/setup/track",
    preset: "fresh",
  },
  experience: {
    code: "O3",
    name: "Prior experience",
    flow: "onboarding",
    stage: "Cold start",
    why: "Self-reported experience sets the prior mastery P(L₀) for concepts the placement quiz does not test. It's one tap with three plain options.",
    system: "Sets the BKT prior: new = 0.12, a little = 0.30, experienced = 0.45.",
    route: "/learner/setup/experience",
    preset: "fresh",
  },
  placement: {
    code: "O4",
    name: "Placement quiz",
    flow: "onboarding",
    stage: "Cold start",
    why: 'Six low-stakes questions, one per foundational concept. "I\'m not sure" is always offered, so learners don\'t guess. A guess is noise for the model; "not sure" is signal.',
    system: "Each answer runs one BKT update on the tagged concepts, seeding the mastery model before any real usage data exists.",
    api: "POST /learners/{id}/onboarding",
    route: "/learner/placement",
    preset: "fresh",
  },
  start: {
    code: "O5",
    name: "Starting point",
    flow: "onboarding",
    stage: "Cold start → System response",
    why: "This reuses the Recommendation Card pattern from S3, so the interface feels consistent from day one. It explains any skipped modules in plain words.",
    system: "Start = first module that has a weak (< 0.6) or unobserved concept.",
    route: "/learner/start",
    preset: "onboarded",
  },
  home: {
    code: "H",
    name: "Home: one next step",
    flow: "learner",
    stage: "User goal",
    why: "Home is not a dashboard. It shows exactly one next action, a trainer-waiting notice when relevant, and unread messages. Everything else lives one tap away in Progress.",
    route: "/learner/home",
    preset: "onboarded",
  },
  quiz: {
    code: "S1",
    name: "Assessment (quick check)",
    flow: "learner",
    stage: "User goal / Task",
    why: 'One question per screen, with 52px tap targets, read-aloud, and figures for visual questions. It\'s framed as a quick check, not a test. A due spaced re-check can be slipped in as question 2, labelled only as "a quick one from earlier" (workflow C).',
    system: "Captures the response stream {learner_id, module_id, question_id, concept_tags[], is_correct, unsure, attempt_number, timestamp}.",
    api: "POST /responses (batch)",
    route: "/learner/quiz/m3",
    preset: "onboarded",
  },
  results: {
    code: "S2",
    name: "Results & transition",
    flow: "learner",
    stage: "Interaction",
    why: "Encouragement first, then a soft score. The learner taps to see the next step; nothing auto-redirects, so learner agency is preserved. Answer explanations are available but secondary.",
    system: "The knowledge-tracing engine updates P(L) for every tagged concept and resolves the root cause over the concept DAG.",
    api: "← { correct, total, recommendation?, recheck? }",
    route: "/learner/results",
    preset: "gap",
  },
  next: {
    code: "S3",
    name: "Recommendation card",
    flow: "learner",
    stage: "System response",
    why: 'One diagnosis, one prescription, one action, and never a dashboard. "Why this?" makes the root-cause reasoning visible when the gap is a prerequisite. That builds trust without adding clutter.',
    system: "Output: { concept_id, diagnostic_text, recommended_content_id }. Content already tried for this concept is skipped.",
    route: "/learner/next",
    preset: "gap",
  },
  learn: {
    code: "S4",
    name: "Remedial view",
    flow: "learner",
    stage: "Action / Escalation",
    why: 'Bite-sized, step-by-step content with animated circuit highlights, narration and an offline badge. The two feedback choices appear after the last step. A quiet "Stuck?" link is always there, so no one gets trapped.',
    api: "POST /content/{id}/start",
    route: "/learner/learn/ct_diag_walk",
    preset: "gap",
  },
  gotit: {
    code: "S4a",
    name: "Got it → re-check scheduled",
    flow: "learner",
    stage: "Loop closes (provisionally)",
    why: "The self-report is not trusted outright. The learner is told, honestly, that a quick question will come back later.",
    system:
      "Applies the BKT learning transition, then schedules a spaced micro-check with an unseen item for that concept, in a later unrelated module.",
    api: "POST /feedback {type: got_it}",
    route: "/learner/got-it",
    preset: "gap",
  },
  stuck: {
    code: "S5",
    name: "Still stuck → ask a trainer",
    flow: "educator",
    stage: "Escalation",
    why: "Escalation happens immediately and the system never auto-retries. One optional tap says why (unclear, need an example, language), so the trainer gets a head start. Free text is optional, because typing is a barrier.",
    system: "Emits an escalation event: { learner_id, concept_id, prior_attempts[], reason, timestamp }.",
    api: "POST /feedback {type: stuck}",
    route: "/learner/stuck",
    preset: "gap",
  },
  helpsent: {
    code: "S5b",
    name: "Help requested",
    flow: "educator",
    stage: "Escalation",
    why: "This closes the uncertainty for the learner: who was told, when to expect a reply, and that they can keep learning meanwhile. It fills a gap in the Sprint 1 flow, which gave no confirmation.",
    route: "/learner/help-sent",
    preset: "escalated",
  },
  progress: {
    code: "P",
    name: "My skill path",
    flow: "learner",
    stage: "Orientation",
    why: 'Mastery is shown as words and icons (Strong / Getting there / Needs practice), never as probabilities. "Confirmed" appears only after a passed spaced re-check.',
    route: "/learner/progress",
    preset: "recheck",
  },
  messages: {
    code: "M",
    name: "Messages from trainer",
    flow: "educator",
    stage: "Resolution reaches learner",
    why: "The educator's resolution comes back to the learner here: a tip, reassigned content in one tap, and an in-person check-in time.",
    route: "/learner/messages",
    preset: "resolved",
  },
  "e-queue": {
    code: "E1",
    name: "Triage queue",
    flow: "educator",
    stage: "Escalation triage",
    why: "Only cases automation couldn't resolve are listed. They're pre-diagnosed and sorted by an explained priority (repeat gap > fixes tried > waiting time). There are no raw logs. \"Common gaps\" suggests a group recap when several learners share a gap.",
    api: "GET /escalations?status=open",
    route: "/educator",
    preset: "escalated",
  },
  "e-case": {
    code: "E2",
    name: "Learner detail & resolution",
    flow: "educator",
    stage: "Escalation triage → Resolve",
    why: "It shows what the system inferred, how confident it is, and what was already tried, so the trainer doesn't repeat a fix that failed. Resolution combines a tip, different content and a check-in in one send.",
    api: "POST /escalations/{id}/resolve",
    route: "/educator",
    preset: "escalated",
  },
  "e-resolved": {
    code: "E3",
    name: "Resolved log",
    flow: "educator",
    stage: "Audit",
    why: "Keeps a light record of what worked. This becomes evaluation data: which interventions resolve which gaps.",
    route: "/educator/resolved",
    preset: "resolved",
  },
};
