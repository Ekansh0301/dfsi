/**
 * Shared data contract between the UI and the (future) FastAPI backend.
 * Field names follow the Sprint 1 Design Doc §5 (Knowledge Tracing & Recommendation Engine).
 * In this prototype the contract is served by `mockServer.ts`; in Sprint 2+ the same
 * shapes are returned by the real service, so screens do not change.
 */

export type Lang = "en" | "hi";
/** A learner-facing string in every supported language. */
export type L = Record<Lang, string>;

export type ConceptId = "safety" | "quantities" | "ohm" | "symbols" | "wiring" | "series_parallel" | "diagrams" | "multimeter" | "earthing" | "fault";

export interface Concept {
  id: ConceptId;
  name: L;
  /** Prerequisite concepts: edges of the concept dependency DAG. */
  prereqs: ConceptId[];
  /** Layout hint for the concept map (column = depth, row = position). */
  pos: { col: number; row: number };
}

export interface Module {
  id: string;
  number: number;
  title: L;
  concepts: ConceptId[];
  /** Question ids of the module's end-of-module quick check. */
  quiz: string[];
  minutes: number;
}

export type FigureId =
  | "sym-switch"
  | "sym-lamp"
  | "sym-cell"
  | "sym-resistor"
  | "circuit-simple"
  | "circuit-series"
  | "circuit-parallel"
  | "circuit-two-switch"
  | "meter-dial";

export interface Option {
  text: L;
  figure?: FigureId;
}

export interface Question {
  id: string;
  concepts: ConceptId[];
  prompt: L;
  figure?: FigureId;
  /** Switches drawn closed in the question figure. */
  figureClosed?: string[];
  options: Option[];
  correct: number;
  /** Plain-language explanation shown after the quiz. */
  why: L;
}

export type ContentKind = "walkthrough" | "video" | "practice";

export interface ContentStep {
  text: L;
  /** Overrides the item-level figure for this step. */
  figure?: FigureId;
  /** Which parts of the figure to highlight (`data-part` names inside the figure SVG). */
  highlight?: string[];
  /** Draw switches closed (all, or the named ones) and animate current flow. */
  closed?: boolean | string[];
  /** Practice steps: revealed after the learner tries. */
  answer?: L;
}

export interface ContentItem {
  id: string;
  concept: ConceptId;
  kind: ContentKind;
  title: L;
  minutes: number;
  figure?: FigureId;
  steps: ContentStep[];
  /** Smaller file, available offline (cached with the app shell). */
  offline: boolean;
}

/** Design Doc §5 input: one row of the response stream. */
export interface ResponseEvent {
  learner_id: string;
  module_id: string;
  question_id: string;
  concept_tags: ConceptId[];
  is_correct: boolean;
  /** Learner tapped "I'm not sure" instead of guessing. */
  unsure: boolean;
  attempt_number: number;
  timestamp: number;
}

/** Design Doc §5 output: one prioritised recommendation. */
export interface Recommendation {
  concept_id: ConceptId;
  /** The concept the learner actually got wrong (may differ from the root cause). */
  observed_concept_id: ConceptId;
  diagnostic_text: L;
  recommended_content_id: string;
  /** Root-cause chain, e.g. ["diagrams", "symbols"] = diagrams is blocked by symbols. */
  chain: ConceptId[];
  strong_concept_id?: ConceptId;
  repeat_gap: boolean;
  created_at: number;
  /** Set when an educator assigned this content while resolving an escalation. */
  from_trainer?: string;
}

export type StuckReason = "unclear" | "need_example" | "language" | "other";

/** Design Doc §5 output: escalation event for the educator queue. */
export interface Escalation {
  id: string;
  learner_id: string;
  concept_id: ConceptId;
  prior_attempts: { content_id: string; at: number; outcome: "stuck" | "recheck_failed" }[];
  reason?: StuckReason;
  note?: string;
  repeat_gap: boolean;
  timestamp: number;
  status: "open" | "resolved";
  resolution?: Resolution;
}

export interface Resolution {
  tip?: string;
  assigned_content_id?: string;
  checkin?: string;
  resolved_by: string;
  at: number;
}

export interface Message {
  id: string;
  learner_id: string;
  from: string;
  text: string;
  assigned_content_id?: string;
  checkin?: string;
  concept_id: ConceptId;
  at: number;
  read: boolean;
}

export interface Recheck {
  concept_id: ConceptId;
  question_id: string;
  scheduled_at: number;
  /** Earliest time it may appear. Demo controls can fast-forward the clock. */
  due_at: number;
  status: "scheduled" | "passed" | "failed";
}

export interface LearnerState {
  id: string;
  name: string;
  cohort: string;
  lang: Lang;
  onboarded: boolean;
  track?: string;
  experience?: "new" | "some" | "experienced";
  /** Per-concept mastery probability P(L) in [0, 1]. */
  mastery: Partial<Record<ConceptId, number>>;
  /** Number of observations per concept, used for the confidence shown to educators. */
  observations: Partial<Record<ConceptId, number>>;
  confirmed: ConceptId[];
  completedModules: string[];
  currentModule: string;
  responses: ResponseEvent[];
  recommendation?: Recommendation;
  /** Content already tried per concept, so the same fix is never recommended the same fix twice. */
  tried: Partial<Record<ConceptId, string[]>>;
  rechecks: Recheck[];
  lastQuiz?: { module_id: string; answers: { question_id: string; chosen: number | null; correct: boolean }[] };
}

export interface DB {
  version: number;
  /** Simulated clock offset (ms) for the demo "fast-forward" support. */
  clockOffset: number;
  learners: Record<string, LearnerState>;
  escalations: Escalation[];
  messages: Message[];
  activeLearnerId: string;
}
