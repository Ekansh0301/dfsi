/**
 * Client-side stand-in for the Knowledge Tracing & Recommendation Engine (Design Doc §5).
 *
 * This exists so the prototype behaves like the real product during demos and user
 * testing. It is deliberately simple and mirrors the v1 backend plan:
 *   1. Bayesian Knowledge Tracing per concept (standard 4-parameter BKT).
 *   2. Multi-concept questions update every tagged concept (naive credit assignment;
 *      the backend will refine this).
 *   3. Root-cause search walks the concept DAG from the observed weak concept to its
 *      weakest unmastered prerequisite.
 *   4. Exactly one content item is resolved, skipping anything already tried.
 * The Sprint 2 FastAPI service replaces this module behind the same `mockServer` API.
 */
import type { ConceptId, L, LearnerState, Recommendation } from "../api/types";
import { CONCEPTS, CONCEPT_ORDER } from "../data/curriculum";
import { contentFor } from "../data/content";

export const BKT = { pInit: 0.25, pLearn: 0.12, pSlip: 0.1, pGuess: 0.2 };
/** P(L) at or above this is treated as "strong". */
export const STRONG = 0.8;
/** P(L) below this is treated as a gap. */
export const WEAK = 0.6;

export function bktUpdate(pL: number, correct: boolean, unsure = false): number {
  const { pLearn, pSlip, pGuess } = BKT;
  // "I'm not sure" is evidence of non-mastery but without the chance of a lucky guess.
  const guess = unsure ? 0.02 : pGuess;
  const posterior = correct ? (pL * (1 - pSlip)) / (pL * (1 - pSlip) + (1 - pL) * guess) : (pL * pSlip) / (pL * pSlip + (1 - pL) * (1 - guess));
  return clamp(posterior + (1 - posterior) * pLearn);
}

/** A remedial activity is a learning opportunity: apply only the transition step. */
export const learnStep = (pL: number) => clamp(pL + (1 - pL) * BKT.pLearn);

const clamp = (x: number) => Math.min(0.99, Math.max(0.01, x));

export const masteryOf = (l: LearnerState, c: ConceptId) => l.mastery[c] ?? BKT.pInit;

export type Band = "strong" | "getting" | "practice" | "new";
export function band(l: LearnerState, c: ConceptId): Band {
  if (!l.observations[c]) return "new";
  const p = masteryOf(l, c);
  return p >= STRONG ? "strong" : p >= WEAK ? "getting" : "practice";
}

/** Walk prerequisites from `c` to the deepest weak concept blocking it. */
export function rootCause(l: LearnerState, c: ConceptId, seen = new Set<ConceptId>()): ConceptId[] {
  seen.add(c);
  const weakPrereqs = CONCEPTS[c].prereqs
    .filter((p) => !seen.has(p) && masteryOf(l, p) < WEAK && (l.observations[p] ?? 0) > 0)
    .sort((a, b) => masteryOf(l, a) - masteryOf(l, b));
  if (weakPrereqs.length === 0) return [c];
  return [c, ...rootCause(l, weakPrereqs[0], seen)];
}

export function pickContent(l: LearnerState, c: ConceptId): string {
  const tried = l.tried[c] ?? [];
  const items = contentFor(c);
  return (items.find((i) => !tried.includes(i.id)) ?? items[0]).id;
}

/**
 * Build the single prioritised recommendation for the concepts just assessed.
 * Returns undefined when nothing is below the gap threshold.
 */
export function recommend(l: LearnerState, assessed: ConceptId[], now: number, repeat = false): Recommendation | undefined {
  // The observed gap is the most advanced weak concept (deepest in the DAG); the root-cause
  // search then walks back to whichever prerequisite is actually blocking it.
  const gaps = assessed
    .filter((c) => masteryOf(l, c) < WEAK)
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
