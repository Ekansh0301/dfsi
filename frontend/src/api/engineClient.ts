import { useSyncExternalStore } from "react";
import type { ConceptId, Recommendation } from "./types";

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

export type EngineMode = "local" | "api" | "fallback";
let mode: EngineMode = BASE ? "api" : "local";
const listeners = new Set<() => void>();
function setMode(m: EngineMode) {
  if (m === mode) return;
  mode = m;
  listeners.forEach((l) => l());
}
export const useEngineMode = () =>
  useSyncExternalStore(
    (fn) => {
      listeners.add(fn);
      return () => void listeners.delete(fn);
    },
    () => mode,
    () => mode,
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
}

async function post<T>(path: string, body: unknown): Promise<T | null> {
  if (!BASE) return null;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 4000);
  try {
    const res = await fetch(BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    if (!res.ok) throw new Error(String(res.status));
    setMode("api");
    return (await res.json()) as T;
  } catch {
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

export const remoteGotIt = (state: EngineState, concept_id: ConceptId) => post<{ state: EngineState }>("/v1/got-it", { state, concept_id });
