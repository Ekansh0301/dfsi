/**
 * Mock backend for the prototype. It runs entirely in the browser and persists to localStorage,
 * so the learner app and educator console share one state, across tabs and the
 * side-by-side demo iframes.
 *
 * Every exported async function corresponds to a planned FastAPI endpoint (noted in the
 * comment above it). Screens only talk to this module. Swapping it for `fetch` calls in
 * Sprint 2 leaves the UI unchanged.
 */
import type { ConceptId, DB, Escalation, Lang, LearnerState, Recommendation, Resolution, StuckReason } from "./types";
import { CONCEPTS, MODULES, PLACEMENT, QUESTIONS, moduleById } from "../data/curriculum";
import { ACTIVE_ID, DB_VERSION, EDUCATOR, seedDB } from "../data/seed";
import { BKT, WEAK, bktUpdate, diagnostic, learnStep, masteryOf, pickContent, recommend } from "../engine/engine";

const KEY = "circuit-coach.db";
const listeners = new Set<() => void>();
let db: DB = load();

function load(): DB {
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as DB;
      if (parsed.version === DB_VERSION) return parsed;
    }
  } catch {
    /* storage blocked (private mode): fall back to in-memory */
  }
  return seedDB(Date.now());
}

function commit(next: DB) {
  db = next;
  try {
    localStorage.setItem(KEY, JSON.stringify(db));
  } catch {
    /* in-memory only */
  }
  listeners.forEach((l) => l());
}

if (typeof window !== "undefined") {
  window.addEventListener("storage", (e) => {
    if (e.key !== KEY) return;
    db = load();
    listeners.forEach((l) => l());
  });
}

export const getDB = () => db;
export const subscribe = (fn: () => void) => {
  listeners.add(fn);
  return () => listeners.delete(fn);
};
export const now = (d: DB = db) => Date.now() + d.clockOffset;

/** Apply a mutation to a copy of the DB and commit it atomically. */
function mutate<R>(fn: (d: DB) => R): R {
  const draft = structuredClone(db);
  const r = fn(draft);
  commit(draft);
  return r;
}
const me = (d: DB) => d.learners[d.activeLearnerId];
const latency = (ms = 450) => new Promise((r) => setTimeout(r, ms));
const uid = () => Math.random().toString(36).slice(2, 9);

// ─── Core logic (sync, reused by presets) ────────────────────────────────────

export interface Answer {
  question_id: string;
  /** null = "I'm not sure" */
  chosen: number | null;
}

function record(d: DB, l: LearnerState, moduleId: string, a: Answer) {
  const q = QUESTIONS[a.question_id];
  const correct = a.chosen === q.correct;
  const unsure = a.chosen === null;
  const attempt = l.responses.filter((r) => r.question_id === q.id).length + 1;
  l.responses.push({
    learner_id: l.id,
    module_id: moduleId,
    question_id: q.id,
    concept_tags: q.concepts,
    is_correct: correct,
    unsure,
    attempt_number: attempt,
    timestamp: now(d),
  });
  for (const c of q.concepts) {
    l.mastery[c] = bktUpdate(masteryOf(l, c), correct, unsure);
    l.observations[c] = (l.observations[c] ?? 0) + 1;
  }
  return correct;
}

function onboardSync(d: DB, experience: LearnerState["experience"], answers: Answer[]) {
  const l = me(d);
  const prior = experience === "new" ? 0.12 : experience === "experienced" ? 0.45 : BKT.pInit + 0.05;
  for (const c of Object.keys(CONCEPTS) as ConceptId[]) l.mastery[c] = prior;
  for (const a of answers) record(d, l, "placement", a);
  l.onboarded = true;
  l.track = "electrical";
  l.experience = experience;
  // Start at the first module with an unobserved or weak concept.
  const start = MODULES.find((m) => m.concepts.some((c) => !l.observations[c] || masteryOf(l, c) < WEAK)) ?? MODULES[0];
  l.completedModules = MODULES.filter((m) => m.number < start.number).map((m) => m.id);
  l.currentModule = start.id;
  return start.id;
}

/** GET /modules/{id}/quiz: the module quiz, with a due spaced re-check interleaved as question 2 (Workflow C). */
export function quizFor(d: DB, moduleId: string): { questions: string[]; recheck?: ConceptId } {
  const m = moduleById(moduleId);
  const l = me(d);
  const rc = l.rechecks.find((r) => r.status === "scheduled" && !m.concepts.includes(r.concept_id) && now(d) >= r.due_at);
  if (!rc) return { questions: m.quiz };
  const qs = [...m.quiz];
  qs.splice(1, 0, rc.question_id);
  return { questions: qs, recheck: rc.concept_id };
}

export interface QuizResult {
  correct: number;
  total: number;
  recommendation?: Recommendation;
  recheck?: { concept: ConceptId; passed: boolean };
  nextModule?: string;
}

function submitQuizSync(d: DB, moduleId: string, answers: Answer[]): QuizResult {
  const l = me(d);
  const m = moduleById(moduleId);
  const t = now(d);
  let correct = 0;
  let recheck: QuizResult["recheck"];
  const graded: NonNullable<LearnerState["lastQuiz"]>["answers"] = [];

  for (const a of answers) {
    const ok = record(d, l, moduleId, a);
    graded.push({ question_id: a.question_id, chosen: a.chosen, correct: ok });
    const rc = m.quiz.includes(a.question_id) ? undefined : l.rechecks.find((r) => r.status === "scheduled" && r.question_id === a.question_id);
    if (rc) {
      rc.status = ok ? "passed" : "failed";
      recheck = { concept: rc.concept_id, passed: ok };
      if (ok && !l.confirmed.includes(rc.concept_id)) l.confirmed.push(rc.concept_id);
      continue; // re-check items don't count toward the module score
    }
    if (ok) correct++;
  }

  l.lastQuiz = { module_id: moduleId, answers: graded };
  if (!l.completedModules.includes(moduleId)) l.completedModules.push(moduleId);
  const next = MODULES.find((x) => !l.completedModules.includes(x.id));
  l.currentModule = next?.id ?? moduleId;

  let rec: Recommendation | undefined;
  if (recheck && !recheck.passed) {
    // Repeat gap: automation has already failed once. Re-route with different content AND tell the trainer.
    const c = recheck.concept;
    rec = recommend(l, [c], t, true) ?? {
      concept_id: c,
      observed_concept_id: c,
      chain: [c],
      diagnostic_text: diagnostic(c, c, undefined, true),
      recommended_content_id: pickContent(l, c),
      repeat_gap: true,
      created_at: t,
    };
    escalate(d, l, c, { outcome: "recheck_failed", repeat: true });
  } else {
    rec = recommend(l, m.concepts, t);
  }
  l.recommendation = rec;
  return { correct, total: m.quiz.length, recommendation: rec, recheck, nextModule: next?.id };
}

function startContentSync(d: DB, contentId: string, concept: ConceptId) {
  const l = me(d);
  const list = (l.tried[concept] ??= []);
  if (!list.includes(contentId)) list.push(contentId);
}

function gotItSync(d: DB) {
  const l = me(d);
  const rec = l.recommendation;
  if (!rec) return;
  const c = rec.concept_id;
  l.mastery[c] = learnStep(masteryOf(l, c));
  // Don't trust the self-report: schedule a spaced check on a question not seen yet.
  // Prefer an unseen item whose main concept is `c` and that no module quiz uses.
  const seen = new Set(l.responses.map((r) => r.question_id));
  const inQuiz = new Set(MODULES.flatMap((m) => m.quiz));
  const primary = Object.values(QUESTIONS).filter((q) => q.concepts[0] === c);
  const q =
    primary.find((x) => !seen.has(x.id) && !inQuiz.has(x.id)) ??
    primary.find((x) => !seen.has(x.id)) ??
    primary.find((x) => !inQuiz.has(x.id)) ??
    primary[0];
  l.rechecks = l.rechecks.filter((r) => !(r.concept_id === c && r.status === "scheduled"));
  l.rechecks.push({ concept_id: c, question_id: q.id, scheduled_at: now(d), due_at: now(d), status: "scheduled" });
  l.recommendation = undefined;
}

function escalate(
  d: DB,
  l: LearnerState,
  concept: ConceptId,
  o: { outcome: "stuck" | "recheck_failed"; repeat?: boolean; reason?: StuckReason; note?: string; content?: string },
) {
  const t = now(d);
  const content = o.content ?? l.tried[concept]?.slice(-1)[0] ?? pickContent(l, concept);
  const open = d.escalations.find((e) => e.status === "open" && e.learner_id === l.id && e.concept_id === concept);
  const attempt = { content_id: content, at: t, outcome: o.outcome };
  if (open) {
    open.prior_attempts.push(attempt);
    open.repeat_gap ||= !!o.repeat;
    open.reason = o.reason ?? open.reason;
    open.note = o.note || open.note;
    open.timestamp = t;
    return open;
  }
  const esc: Escalation = {
    id: "esc_" + uid(),
    learner_id: l.id,
    concept_id: concept,
    prior_attempts: [attempt],
    reason: o.reason,
    note: o.note,
    repeat_gap: !!o.repeat || l.rechecks.some((r) => r.concept_id === concept && r.status === "failed"),
    timestamp: t,
    status: "open",
  };
  d.escalations.unshift(esc);
  return esc;
}

function stuckSync(d: DB, reason: StuckReason, note: string) {
  const l = me(d);
  const rec = l.recommendation;
  if (!rec) return;
  escalate(d, l, rec.concept_id, { outcome: "stuck", reason, note, content: rec.recommended_content_id, repeat: rec.repeat_gap });
  l.recommendation = undefined; // never auto-retry: the next step now belongs to a human
}

function resolveSync(d: DB, escId: string, r: Omit<Resolution, "resolved_by" | "at">) {
  const esc = d.escalations.find((e) => e.id === escId);
  if (!esc) return;
  const t = now(d);
  esc.status = "resolved";
  esc.resolution = { ...r, resolved_by: EDUCATOR.name, at: t };
  const l = d.learners[esc.learner_id];
  d.messages.unshift({
    id: "msg_" + uid(),
    learner_id: l.id,
    from: EDUCATOR.name,
    text: r.tip ?? "",
    assigned_content_id: r.assigned_content_id,
    checkin: r.checkin,
    concept_id: esc.concept_id,
    at: t,
    read: false,
  });
  if (r.assigned_content_id) {
    l.recommendation = {
      concept_id: esc.concept_id,
      observed_concept_id: esc.concept_id,
      chain: [esc.concept_id],
      diagnostic_text: {
        en: `${EDUCATOR.name} picked this for you on ${CONCEPTS[esc.concept_id].name.en.toLowerCase()}.`,
        hi: `${EDUCATOR.name} ने ${CONCEPTS[esc.concept_id].name.hi} के लिए यह आपके लिए चुना है।`,
      },
      recommended_content_id: r.assigned_content_id,
      repeat_gap: esc.repeat_gap,
      created_at: t,
      from_trainer: EDUCATOR.name,
    };
  }
}

// ─── Public API (one function per planned endpoint) ──────────────────────────

/** PATCH /learners/{id} */
export const setLang = (lang: Lang) => mutate((d) => void (me(d).lang = lang));

/** POST /learners/{id}/onboarding → { start_module_id } */
export async function finishOnboarding(experience: LearnerState["experience"], answers: Answer[]) {
  await latency(900);
  return mutate((d) => onboardSync(d, experience, answers));
}

/** POST /responses (batch) → { correct, total, recommendation?, recheck? } */
export async function submitQuiz(moduleId: string, answers: Answer[]) {
  await latency(250);
  return mutate((d) => submitQuizSync(d, moduleId, answers));
}

/** POST /content/{id}/start */
export const startContent = (contentId: string, concept: ConceptId) => mutate((d) => startContentSync(d, contentId, concept));

/** POST /feedback { type: "got_it" } → schedules a spaced re-check */
export async function gotIt() {
  await latency(300);
  mutate(gotItSync);
}

/** POST /feedback { type: "stuck" } → Escalation event */
export async function stuck(reason: StuckReason, note: string) {
  await latency(600);
  mutate((d) => stuckSync(d, reason, note));
}

/** POST /escalations/{id}/resolve → message to learner, optional content assignment */
export async function resolveEscalation(escId: string, r: Omit<Resolution, "resolved_by" | "at">) {
  await latency(500);
  mutate((d) => resolveSync(d, escId, r));
}

export const markMessagesRead = () => mutate((d) => d.messages.forEach((m) => m.learner_id === d.activeLearnerId && (m.read = true)));

export const fastForward = (hours: number) => mutate((d) => void (d.clockOffset += hours * 3600_000));

export const setRecommendationFromMessage = (msgId: string) =>
  mutate((d) => {
    const m = d.messages.find((x) => x.id === msgId);
    if (!m?.assigned_content_id) return;
    const l = me(d);
    l.recommendation = {
      concept_id: m.concept_id,
      observed_concept_id: m.concept_id,
      chain: [m.concept_id],
      diagnostic_text: {
        en: `${m.from} picked this for you on ${CONCEPTS[m.concept_id].name.en.toLowerCase()}.`,
        hi: `${m.from} ने ${CONCEPTS[m.concept_id].name.hi} के लिए यह आपके लिए चुना है।`,
      },
      recommended_content_id: m.assigned_content_id,
      repeat_gap: false,
      created_at: now(d),
      from_trainer: m.from,
    };
  });

// ─── Educator-side derived data ──────────────────────────────────────────────

export interface Priority {
  score: number;
  level: "high" | "medium" | "normal";
  reasons: { en: string }[];
}

/** Triage priority: repeat gaps first, then failed fixes, then waiting time. */
export function priorityOf(e: Escalation, d: DB = db): Priority {
  const hours = (now(d) - e.timestamp) / 3600_000;
  const fixes = e.prior_attempts.length;
  let score = 1 + fixes + Math.min(hours / 12, 2);
  const reasons: { en: string }[] = [];
  if (e.repeat_gap) {
    score += 3;
    reasons.push({ en: "Repeat gap" });
  }
  if (fixes > 1) reasons.push({ en: `${fixes} fixes tried` });
  if (e.reason === "language") {
    score += 0.5;
    reasons.push({ en: "Language barrier" });
  }
  if (hours >= 3) reasons.push({ en: `Waiting ${hours >= 24 ? Math.floor(hours / 24) + "d" : Math.floor(hours) + "h"}` });
  return { score, level: score >= 5 ? "high" : score >= 2.8 ? "medium" : "normal", reasons };
}

/** Concepts where several learners in the batch are below the gap threshold. */
export function cohortGaps(d: DB = db) {
  const ls = Object.values(d.learners).filter((l) => l.onboarded);
  return (Object.keys(CONCEPTS) as ConceptId[])
    .map((c) => {
      const observed = ls.filter((l) => l.observations[c]);
      const weak = observed.filter((l) => masteryOf(l, c) < WEAK);
      return { concept: c, weak: weak.map((l) => l.id), observed: observed.length };
    })
    .filter((g) => g.weak.length >= 2)
    .sort((a, b) => b.weak.length - a.weak.length);
}

// ─── Demo presets (jump straight to any point of any flow) ──────────────────

export type Preset = "fresh" | "onboarded" | "gap" | "rootcause" | "escalated" | "resolved" | "recheck";

const PLACEMENT_GOOD: Answer[] = PLACEMENT.map((id) => ({ question_id: id, chosen: QUESTIONS[id].correct }));
/** Module 3 with diagram questions wrong → "diagrams seem tricky" (Sprint 1 story). */
const M3_DIAGRAM_GAP: Answer[] = [
  { question_id: "q_w1", chosen: 1 },
  { question_id: "q_w2", chosen: 0 },
  { question_id: "q_w3", chosen: 1 },
  { question_id: "q_w4", chosen: 2 },
  { question_id: "q_w5", chosen: 0 },
];
/** Module 3 with the symbol question also wrong → root cause is a prerequisite. */
const M3_SYMBOL_ROOT: Answer[] = [
  { question_id: "q_w1", chosen: 0 },
  { question_id: "q_w2", chosen: 0 },
  { question_id: "q_w3", chosen: null },
  { question_id: "q_w4", chosen: 2 },
  { question_id: "q_w5", chosen: 0 },
];

export function applyPreset(p: Preset) {
  const d = seedDB(Date.now());
  const steps: Record<Preset, number> = { fresh: 0, onboarded: 1, gap: 2, rootcause: 2, escalated: 3, resolved: 4, recheck: 5 };
  const n = steps[p];
  if (n >= 1)
    onboardSync(d, "some", p === "rootcause" ? PLACEMENT_GOOD.map((a) => (a.question_id === "q_x_sym2" ? { ...a, chosen: 2 } : a)) : PLACEMENT_GOOD);
  if (n >= 2) submitQuizSync(d, "m3", p === "rootcause" ? M3_SYMBOL_ROOT : M3_DIAGRAM_GAP);
  const rec = d.learners[ACTIVE_ID].recommendation;
  if (n >= 3 && rec) startContentSync(d, rec.recommended_content_id, rec.concept_id);
  if (p === "escalated" || p === "resolved") stuckSync(d, "unclear", "The symbols make sense but I lose track of which wire goes where");
  if (p === "resolved") {
    const esc = d.escalations.find((e) => e.learner_id === ACTIVE_ID)!;
    resolveSync(d, esc.id, {
      tip: "Use two fingers: one stays on +, the other walks the wire. If it can't get back to −, the lamp is off.",
      assigned_content_id: "ct_diag_practice",
      checkin: "Tomorrow, 10:00 in the lab",
    });
  }
  if (p === "recheck") {
    gotItSync(d);
    submitQuizSync(d, "m4", [
      { question_id: "q_p1", chosen: 0 },
      { question_id: "q_p2", chosen: 0 },
      { question_id: "q_p3", chosen: 0 },
    ]);
    d.learners[ACTIVE_ID].recommendation = undefined;
  }
  commit(d);
}

export const resetDemo = () => applyPreset("fresh");
