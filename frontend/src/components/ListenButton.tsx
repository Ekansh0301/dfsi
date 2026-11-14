import { useEffect, useState } from "react";
import { Square, Volume2 } from "lucide-react";
import type { Lang } from "../api/types";
import { useT } from "../lib/i18n";

/**
 * Reads text aloud with the browser's built-in speech (Hindi or English, following the
 * learner's language). Nothing is downloaded and no outside service is called. The button is
 * hidden when the device has no voice for the language. Pre-recorded natural audio can replace
 * the speech later without changing where the button sits.
 */

type VoiceLike = Pick<SpeechSynthesisVoice, "lang" | "localService" | "name">;

/** The best voice for a language: an Indian voice first, then any voice for the language. */
export function pickVoice<V extends VoiceLike>(voices: readonly V[], lang: Lang): V | undefined {
  const norm = (l: string) => l.toLowerCase().replace("_", "-");
  const want = lang === "hi" ? ["hi-in", "hi"] : ["en-in", "en-gb", "en-us", "en"];
  for (const w of want) {
    const exact = voices.filter((v) => norm(v.lang) === w || (w.length === 2 && norm(v.lang).startsWith(w + "-")));
    if (exact.length) return exact.find((v) => /natural|neural|online/i.test(v.name)) ?? exact.find((v) => v.localService) ?? exact[0];
  }
  return undefined;
}

const synth = (): SpeechSynthesis | undefined => (typeof window !== "undefined" && "speechSynthesis" in window ? window.speechSynthesis : undefined);

/** The voice for `lang` once the browser has loaded its voice list, or undefined if there is none. */
export function useVoice(lang: Lang): SpeechSynthesisVoice | undefined {
  const [voice, setVoice] = useState<SpeechSynthesisVoice | undefined>(() => {
    const s = synth();
    return s ? pickVoice(s.getVoices(), lang) : undefined;
  });
  useEffect(() => {
    const s = synth();
    if (!s) return;
    const update = () => setVoice(pickVoice(s.getVoices(), lang));
    update();
    s.addEventListener("voiceschanged", update);
    return () => s.removeEventListener("voiceschanged", update);
  }, [lang]);
  return voice;
}

export function ListenButton({ text, className = "" }: { text: string; className?: string }) {
  const { t, lang } = useT();
  const voice = useVoice(lang);
  const [speaking, setSpeaking] = useState(false);

  // Stop when the text changes (next question or step) or the screen closes.
  useEffect(() => {
    return () => {
      synth()?.cancel();
      setSpeaking(false);
    };
  }, [text]);

  if (!voice) return null;

  const toggle = () => {
    const s = synth();
    if (!s) return;
    s.cancel();
    if (speaking) {
      setSpeaking(false);
      return;
    }
    const u = new SpeechSynthesisUtterance(text);
    u.voice = voice;
    u.lang = voice.lang;
    u.rate = 0.92;
    u.onend = u.onerror = () => setSpeaking(false);
    setSpeaking(true);
    s.speak(u);
  };

  return (
    <button
      type="button"
      className={"btn btn-ghost listen-btn " + className}
      onClick={toggle}
      aria-pressed={speaking}
      aria-label={speaking ? t("listen_stop") : t("listen")}
      title={speaking ? t("listen_stop") : t("listen")}
    >
      {speaking ? <Square size={18} aria-hidden /> : <Volume2 size={20} aria-hidden />}
    </button>
  );
}
