/**
 * The knowledge-tracing and recommendation engine, in the browser.
 *
 * This is the same engine as the service (`backend/circuit_coach/engine.py` and `bkt.py`), step
 * for step, so the app gives the same answers with the service running, with it down, and on the
 * deployed site that has no service:
 *   1. Bayesian Knowledge Tracing per concept, with the fitted parameters the service ships.
 *   2. Question types (true/false and short answers guess differently), partial credit for marked
 *      short answers, retakes that count for less, and per-question difficulty.
 *   3. The improved model: first-tag credit, difficulty, prerequisite-aware learning and more
 *      evidence before a lesson. It is the default, as in the service; the baseline is selectable.
 *   4. Root-cause search walks the concept graph from the observed weak concept to its weakest
 *      unmastered prerequisite, and exactly one lesson is resolved, skipping any already tried.
 * `engine/__tests__/parity.test.ts` replays journeys recorded from the service and requires the
 * same answers.
 */
import type { ConceptId, L, LearnerState, QuestionType, Recommendation } from "../api/types";
import { CONCEPTS, CONCEPT_ORDER, MODULES } from "../data/curriculum";
import { contentFor } from "../data/content";
import fitted from "../data/fittedParams.json";
import difficultyFile from "../data/itemDifficulty.json";

export interface Params {
  pInit: number;
  pLearn: number;
  pSlip: number;
  pGuess: number;
}

/** Hand-set values, the unfitted reference point (`bkt.HAND_SET`). */
export const BKT: Params = { pInit: 0.25, pLearn: 0.12, pSlip: 0.1, pGuess: 0.2 };
/** P(L) at or above this is treated as "strong". */
export const STRONG = 0.8;
/** P(L) below this is treated as a gap. */
export const WEAK = 0.6;

const P_MIN = 0.01;
const P_MAX = 0.99;
/** "I'm not sure" is evidence of not knowing the concept, without the chance of a lucky guess. */
const UNSURE_GUESS = 0.02;
/** Chance of a lucky guess by question type (same values as the service, `bkt.TYPE_GUESS`). */
export const TYPE_GUESS: Partial<Record<QuestionType, number>> = { true_false: 0.5, short_answer: 0.05 };
/** Attempt k of a retaken quiz counts with weight RETAKE_DECAY ** (k - 1). */
export const RETAKE_DECAY = 0.5;

// ─── Models ──────────────────────────────────────────────────────────────────

export interface ModelOptions {
  name: ModelName;
  /** "all": a multi-concept question updates every tag. "first": only its first, main tag. */
  credit: "all" | "first";
  itemDifficulty: boolean;
  /** Learning speed while an observed prerequisite looks unmastered, as a share of the normal rate; 1 switches it off. */
  prereqLearnFactor: number;
  /** Answers on a concept needed before it can trigger a lesson. */
  minEvidence: number;
  /** ...unless its mastery is below this after at least one answer. */
  strongEvidence: number;
}

export type ModelName = "baseline" | "improved";

export const MODELS: Record<ModelName, ModelOptions> = {
  baseline: { name: "baseline", credit: "all", itemDifficulty: false, prereqLearnFactor: 1, minEvidence: 0, strongEvidence: 0 },
  improved: { name: "improved", credit: "first", itemDifficulty: true, prereqLearnFactor: 0.5, minEvidence: 2, strongEvidence: 0.4 },
};

type RawParams = Record<string, { p_init: number; p_learn: number; p_slip: number; p_guess: number }>;
const toParams = (raw: RawParams): Record<ConceptId, Params> =>
  Object.fromEntries(
    CONCEPT_ORDER.map((c) => {
      const p = raw[c];
      return [c, { pInit: p.p_init, pLearn: p.p_learn, pSlip: p.p_slip, pGuess: p.p_guess }];
    }),
  ) as Record<ConceptId, Params>;

/** The improved model is fitted with first-tag credit, so it reads its own set (`load_params`). */
const PARAMS: Record<ModelName, Record<ConceptId, Params>> = {
  baseline: toParams(fitted.concepts),
  improved: toParams(fitted.concepts_first_tag),
};

const envModel = import.meta.env.VITE_ENGINE_MODEL as string | undefined;
/** True when the build pins the model (`VITE_ENGINE_MODEL`); otherwise the browser follows the service's default. */
export const modelPinned = envModel === "baseline" || envModel === "improved";
let active: ModelName = modelPinned ? (envModel as ModelName) : "improved";
let difficulty: Record<string, number> = { ...(difficultyFile.items as Record<string, number>) };

export const modelName = (): ModelName => active;
/** Used by the engine client to follow the service's default model, so the fallback answers the same. */
export function setModel(name: string) {
  if (!modelPinned && (name === "baseline" || name === "improved")) active = name;
}
/** Replace the per-question difficulty table (tests; the shipped table is `data/itemDifficulty.json`). */
export function setItemDifficulty(table: Record<string, number>) {
  difficulty = { ...table };
}

const opts = () => MODELS[active];
const paramsOf = (c: ConceptId): Params => PARAMS[active][c];

// ─── BKT arithmetic (bkt.py) ─────────────────────────────────────────────────

const clamp = (x: number) => Math.min(P_MAX, Math.max(P_MIN, x));
const logit = (x: number) => {
  const y = Math.min(1 - 1e-6, Math.max(1e-6, x));
  return Math.log(y / (1 - y));
};
const sigmoid = (x: number) => 1 / (1 + Math.exp(-x));

/** Slip and guess for one question: a harder one (positive shift) is slipped on more and guessed less. */
function slipGuess(p: Params, type: QuestionType, shift: number): [number, number] {
  let slip = p.pSlip;
  let guess = TYPE_GUESS[type] ?? p.pGuess;
  if (shift) {
    slip = sigmoid(logit(slip) + shift);
    if (!(type in TYPE_GUESS)) guess = sigmoid(logit(guess) - shift);
  }
  return [slip, guess];
}

function posterior(pL: number, correct: boolean, slip: number, guess: number, unsure: boolean): number {
  const g = unsure ? Math.min(guess, UNSURE_GUESS) : guess;
  if (correct) {
    const num = pL * (1 - slip);
    return num / (num + (1 - pL) * g);
  }
  const num = pL * slip;
  return num / (num + (1 - pL) * (1 - g));
}

export interface UpdateOptions {
  type?: QuestionType;
  /** Partial credit 0 to 1 (a marked short answer); replaces `correct`. */
  score?: number;
  attempt?: number;
  difficulty?: number;
  /** Replaces the concept's learning rate for this step. */
  learn?: number;
  params?: Params;
}

/** One full BKT step: condition on the answer (`bkt.update`), then apply the learning transition. */
export function bktUpdate(pL: number, correct: boolean, unsure = false, type: QuestionType = "multiple_choice", score?: number, o: UpdateOptions = {}): number {
  const p = o.params ?? BKT;
  const [slip, guess] = slipGuess(p, type, o.difficulty ?? 0);
  let post: number;
  if (score === undefined) post = posterior(pL, correct, slip, guess, unsure);
  else {
    const s = Math.min(1, Math.max(0, score));
    post = s * posterior(pL, true, slip, guess, false) + (1 - s) * posterior(pL, false, slip, guess, false);
  }
  const w = RETAKE_DECAY ** (Math.max(o.attempt ?? 1, 1) - 1);
  const moved = pL + w * (post - pL);
  return clamp(moved + (1 - moved) * (o.learn ?? p.pLearn));
}

/** A lesson is a learning opportunity: apply only the transition step. */
export const learnStep = (pL: number, c?: ConceptId) => clamp(pL + (1 - pL) * (c ? paramsOf(c).pLearn : BKT.pLearn));

// ─── Learner state and tracing (engine.py) ───────────────────────────────────

/** The part of a learner the model reads and writes. */
export type ModelState = Pick<LearnerState, "mastery" | "observations" | "tried">;

/** One answered question, as the service takes it (`EventModel`). */
export interface EngineEvent {
  concept_tags: ConceptId[];
  is_correct: boolean;
  unsure: boolean;
  question_type: QuestionType;
  /** Partial credit 0 to 1; replaces `is_correct`. */
  score?: number;
  /** 1 for the first try at this question; retakes count for less. */
  attempt_number?: number;
  /** The question's id, for its difficulty. */
  item_id?: string;
}

export const masteryOf = (l: Pick<LearnerState, "mastery">, c: ConceptId) => l.mastery[c] ?? paramsOf(c).pInit;

/** Learning rate for `c` now: slower while its observed prerequisites look weak (S3-5). */
function learnRate(l: ModelState, c: ConceptId): number | undefined {
  const f = opts().prereqLearnFactor;
  if (f >= 1) return undefined;
  let ready = 1;
  for (const p of CONCEPTS[c].prereqs) if (l.observations[p]) ready *= masteryOf(l, p);
  return paramsOf(c).pLearn * (f + (1 - f) * ready);
}

/** Update the learner's mastery and observation counts for the events, in order (changes `l`). */
export function trace(l: ModelState, events: Iterable<EngineEvent>) {
  const o = opts();
  for (const ev of events) {
    let tags = Array.from(new Set(ev.concept_tags)); // a tag listed twice counts once
    if (o.credit === "first") tags = tags.slice(0, 1);
    const shift = o.itemDifficulty && ev.item_id ? (difficulty[ev.item_id] ?? 0) : 0;
    for (const c of tags) {
      if (!(c in CONCEPTS)) continue;
      l.mastery[c] = bktUpdate(masteryOf(l, c), ev.is_correct, ev.unsure, ev.question_type, ev.score, {
        attempt: ev.attempt_number ?? 1,
        difficulty: shift,
        learn: learnRate(l, c),
        params: paramsOf(c),
      });
      l.observations[c] = (l.observations[c] ?? 0) + 1;
    }
  }
}

/** Has the engine seen enough of `c` to send a learner to a lesson on it? (S3-6) */
export function enoughEvidence(l: ModelState, c: ConceptId): boolean {
  const o = opts();
  const n = l.observations[c] ?? 0;
  if (n < 1) return false; // a concept never answered is never a gap
  if (o.minEvidence <= 1) return true;
  return n >= o.minEvidence || masteryOf(l, c) < o.strongEvidence;
}

export const onboardingPrior = (experience: string | undefined) => (experience === "new" ? 0.12 : experience === "experienced" ? 0.45 : 0.3);

export type Band = "strong" | "getting" | "practice" | "new";
export function band(l: LearnerState, c: ConceptId): Band {
  if (!l.observations[c]) return "new";
  const p = masteryOf(l, c);
  return p >= STRONG ? "strong" : p >= WEAK ? "getting" : "practice";
}

/** Walk prerequisites from `c` to the deepest weak concept blocking it. */
export function rootCause(l: ModelState, c: ConceptId, seen = new Set<ConceptId>()): ConceptId[] {
  seen.add(c);
  const weakPrereqs = CONCEPTS[c].prereqs
    .filter((p) => !seen.has(p) && masteryOf(l, p) < WEAK && (l.observations[p] ?? 0) > 0)
    .sort((a, b) => masteryOf(l, a) - masteryOf(l, b));
  if (weakPrereqs.length === 0) return [c];
  return [c, ...rootCause(l, weakPrereqs[0], seen)];
}

export function pickContent(l: Pick<LearnerState, "tried">, c: ConceptId): string {
  const tried = l.tried[c] ?? [];
  const items = contentFor(c);
  return (items.find((i) => !tried.includes(i.id)) ?? items[0]).id;
}

/** The first module with an unobserved or weak concept (`Engine.start_module`). */
export function startModule(l: ModelState): string {
  const m = MODULES.find((x) => x.concepts.some((c) => !l.observations[c] || masteryOf(l, c) < WEAK));
  return (m ?? MODULES[0]).id;
}

/**
 * Build the single prioritised recommendation for the concepts just assessed.
 * Returns undefined when nothing is below the gap threshold.
 */
export function recommend(l: ModelState, assessed: ConceptId[], now: number, repeat = false): Recommendation | undefined {
  // The observed gap is the most advanced weak concept (deepest in the graph, then weakest); the
  // root-cause search then walks back to whichever prerequisite is actually blocking it.
  const gaps = assessed
    .filter((c) => masteryOf(l, c) < WEAK && enoughEvidence(l, c))
    .sort((a, b) => CONCEPTS[b].pos.col - CONCEPTS[a].pos.col || masteryOf(l, a) - masteryOf(l, b));
  if (gaps.length === 0) return undefined;
  const observed = gaps[0];
  const chain = rootCause(l, observed);
  const target = chain[chain.length - 1];
  const strong = assessed
    .filter((c) => c !== observed && !chain.includes(c) && masteryOf(l, c) >= WEAK)
    .sort((a, b) => masteryOf(l, b) - masteryOf(l, a))[0];
  return {
    concept_id: target,
    observed_concept_id: observed,
    chain,
    strong_concept_id: strong,
    diagnostic_text: diagnostic(observed, target, strong, repeat),
    recommended_content_id: pickContent(l, target),
    repeat_gap: repeat,
    created_at: now,
  };
}

/** The learner said "Got it!" but failed the follow-up check: try again, differently. */
export function recommendRepeat(l: ModelState, c: ConceptId, now: number): Recommendation {
  return (
    recommend(l, [c], now, true) ?? {
      concept_id: c,
      observed_concept_id: c,
      chain: [c],
      diagnostic_text: diagnostic(c, c, undefined, true),
      recommended_content_id: pickContent(l, c),
      repeat_gap: true,
      created_at: now,
    }
  );
}

const n = (c: ConceptId) => CONCEPTS[c].name;
const lower = (s: string) => s.charAt(0).toLowerCase() + s.slice(1);

/** Plain-language diagnostic. Never a score, always one concept. */
export function diagnostic(observed: ConceptId, target: ConceptId, strong: ConceptId | undefined, repeat: boolean): L {
  const t = { en: lower(n(target).en), hi: n(target).hi };
  if (repeat)
    return {
      en: `Let's go over ${t.en} again, a different way this time.`,
      hi: `चलिए ${t.hi} को फिर से देखते हैं, इस बार नए तरीके से।`,
    };
  if (observed !== target)
    return {
      en: `You got stuck on ${lower(n(observed).en)}. It builds on ${t.en}, so let's start there.`,
      hi: `आप ${n(observed).hi} में अटके। यह ${t.hi} पर टिका है, इसलिए वहीं से शुरू करते हैं।`,
    };
  if (strong)
    return {
      en: `You did well on ${lower(n(strong).en)}. Now let's take a closer look at ${t.en}.`,
      hi: `${n(strong).hi} में आपने अच्छा किया। अब ${t.hi} को ध्यान से देखते हैं।`,
    };
  return { en: `Let's take a closer look at ${t.en}.`, hi: `चलिए ${t.hi} को ध्यान से देखते हैं।` };
}

/** Educator-facing confidence: how many observations back the estimate. */
export const confidence = (l: LearnerState, c: ConceptId): "low" | "medium" | "high" => {
  const k = l.observations[c] ?? 0;
  return k >= 5 ? "high" : k >= 2 ? "medium" : "low";
};

export const allConcepts = CONCEPT_ORDER;
