import { useEffect, useState } from "react";
import type { Lang } from "../api/types";

/**
 * Read-aloud for low-literacy learners, using the browser's built-in speech synthesis.
 * Degrades gracefully where unsupported. In the field this would be pre-recorded audio.
 */
const synth = typeof window !== "undefined" && "speechSynthesis" in window ? window.speechSynthesis : null;
const listeners = new Set<(id: string | null) => void>();
let speakingId: string | null = null;
/** Incremented on every speak/stop, so callbacks from a cancelled utterance are ignored. */
let seq = 0;
let watchdog: number | undefined;

const set = (id: string | null) => {
  speakingId = id;
  listeners.forEach((l) => l(id));
};

export const speechSupported = !!synth;

export function speak(id: string, text: string, lang: Lang, onEnd?: () => void) {
  const mine = ++seq;
  window.clearTimeout(watchdog);
  const finish = () => {
    if (mine !== seq) return;
    window.clearTimeout(watchdog);
    set(null);
    onEnd?.();
  };
  // Some platforms expose the API without voices and never fire `end`; don't let playback stall.
  watchdog = window.setTimeout(finish, Math.max(3000, text.length * 85));
  set(id);
  if (!synth) return;
  synth.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang === "hi" ? "hi-IN" : "en-IN";
  u.rate = 0.92;
  const voices = synth.getVoices();
  const voice = voices.find((v) => v.lang === u.lang) ?? voices.find((v) => v.lang.startsWith(lang));
  if (voice) u.voice = voice;
  u.onend = finish;
  u.onerror = finish;
  synth.speak(u);
}

export function stopSpeaking() {
  seq++;
  window.clearTimeout(watchdog);
  synth?.cancel();
  set(null);
}

export function useSpeaking(id: string) {
  const [cur, setCur] = useState(speakingId);
  useEffect(() => {
    listeners.add(setCur);
    return () => void listeners.delete(setCur);
  }, []);
  return cur === id;
}
