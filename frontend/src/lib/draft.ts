/**
 * Unfinished quiz answers, kept in localStorage so a reload, a closed tab or a phone that drops
 * the page in the background does not lose them. Cleared on submit and on a demo reset.
 */
const PREFIX = "circuit-coach.draft.";
const MAX_AGE_MS = 24 * 60 * 60 * 1000;

export interface QuizDraft {
  i: number;
  answers: Record<string, number | null>;
  texts: Record<string, string>;
}

const key = (learnerId: string, questions: string[]) => `${PREFIX}${learnerId}.${questions.join(",")}`;

export function loadDraft(learnerId: string, questions: string[]): QuizDraft | null {
  try {
    const raw = localStorage.getItem(key(learnerId, questions));
    if (!raw) return null;
    const d = JSON.parse(raw) as QuizDraft & { at: number };
    if (Date.now() - d.at > MAX_AGE_MS) return null;
    return { i: Math.min(Math.max(0, d.i), questions.length - 1), answers: d.answers ?? {}, texts: d.texts ?? {} };
  } catch {
    return null;
  }
}

export function saveDraft(learnerId: string, questions: string[], draft: QuizDraft) {
  try {
    localStorage.setItem(key(learnerId, questions), JSON.stringify({ ...draft, at: Date.now() }));
  } catch {
    /* storage full or blocked: the quiz still works, it just is not kept */
  }
}

export function clearDraft(learnerId: string, questions: string[]) {
  try {
    localStorage.removeItem(key(learnerId, questions));
  } catch {
    /* ignore */
  }
}

export function clearAllDrafts() {
  try {
    for (let k = localStorage.length - 1; k >= 0; k--) {
      const name = localStorage.key(k);
      if (name?.startsWith(PREFIX)) localStorage.removeItem(name);
    }
  } catch {
    /* ignore */
  }
}
