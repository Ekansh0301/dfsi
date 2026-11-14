import { useSyncExternalStore } from "react";
import type { ConceptId, QuestionType, Recommendation } from "./types";

/**
 * Optional connection to the engine service in `backend/`.
 *
 * Without `VITE_API_URL` the prototype uses its in-browser engine, as before. With it set,
 * the model steps (placement, quiz result, "Got it!") are sent to the service, and the
 * prototype falls back to the in-browser engine if a call fails, so a demo never breaks.
 *
 *   VITE_API_URL=http://localhost:8000 npm run dev
 */
const BASE = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "");
/** Optional engine model on the service: "baseline" or "improved" (VITE_ENGINE_MODEL). */
export const MODEL = (import.meta.env.VITE_ENGINE_MODEL as string | undefined) || undefined;
/** Optional key for a service started with CIRCUIT_COACH_API_KEY (sent as X-API-Key). */
const API_KEY = (import.meta.env.VITE_API_KEY as string | undefined) || undefined;

export type EngineMode = "local" | "checking" | "api" | "fallback";
/** With a service configured the mode starts as "checking" until a health check or a call answers. */
let mode: EngineMode = BASE ? "checking" : "local";
const listeners = new Set<() => void>();
function setMode(m: EngineMode) {
  if (m === mode) return;
  mode = m;
  listeners.forEach((l) => l());
}
export const getEngineMode = () => mode;
export const useEngineMode = () =>
  useSyncExternalStore(
    (fn) => {
      listeners.add(fn);
      return () => void listeners.delete(fn);
    },
    getEngineMode,
    getEngineMode,
  );

export interface EngineState {
  mastery: Partial<Record<ConceptId, number>>;
  observations: Partial<Record<ConceptId, number>>;
  tried: Partial<Record<ConceptId, string[]>>;
}
export interface EngineEvent {
  concept_tags: ConceptId[];
  is_correct: boolean;
  unsure: boolean;
  question_type: QuestionType;
}

/** After a failed call, a quick health check runs first, so a service that is down costs about a
 *  second per step instead of the full 4 second timeout. */
const RETRY_WINDOW_MS = 60_000;
let lastFailure = 0;

async function healthy(timeoutMs: number): Promise<boolean> {
  if (!BASE) return false;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(BASE + "/health", { signal: ctrl.signal });
    return res.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}

/** Ask the service whether it is up and show the answer in the top bar. Called once on start-up. */
export async function checkHealth(): Promise<EngineMode> {
  if (!BASE) return mode;
  const ok = await healthy(3000);
  if (!ok) lastFailure = Date.now();
  setMode(ok ? "api" : "fallback");
  return mode;
}

async function post<T>(path: string, body: unknown): Promise<T | null> {
  if (!BASE) return null;
  if (Date.now() - lastFailure < RETRY_WINDOW_MS && !(await healthy(1200))) {
    lastFailure = Date.now();
    setMode("fallback");
    return null;
  }
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 4000);
  try {
    const res = await fetch(BASE + path + (MODEL ? `?model=${encodeURIComponent(MODEL)}` : ""), {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(API_KEY ? { "X-API-Key": API_KEY } : {}) },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    if (!res.ok) throw new Error(String(res.status));
    setMode("api");
    lastFailure = 0;
    return (await res.json()) as T;
  } catch {
    lastFailure = Date.now();
    setMode("fallback");
    return null;
  } finally {
    clearTimeout(timer);
  }
}

export const remoteOnboarding = (experience: string, events: EngineEvent[]) =>
  post<{ state: EngineState; start_module_id: string }>("/v1/onboarding", { experience, events });

export const remoteQuizResult = (req: { state: EngineState; module_id: string; events: EngineEvent[]; recheck_concept?: ConceptId; now: number }) =>
  post<{ state: EngineState; recommendation: (Omit<Recommendation, "strong_concept_id"> & { strong_concept_id: ConceptId | null }) | null }>(
    "/v1/quiz-result",
    req,
  );

export const remoteMarkedAnswer = (state: EngineState, concept_tags: ConceptId[], score: number, now: number) =>
  post<{ state: EngineState; recommendation: (Omit<Recommendation, "strong_concept_id"> & { strong_concept_id: ConceptId | null }) | null }>(
    "/v1/marked-answer",
    { state, concept_tags, score, now },
  );

export const remoteGotIt = (state: EngineState, concept_id: ConceptId, content_id?: string) =>
  post<{ state: EngineState }>("/v1/got-it", { state, concept_id, content_id });
