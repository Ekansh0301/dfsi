import { useMemo, useState } from "react";
import { ArrowRight, CircleQuestionMark, History } from "lucide-react";
import type { Answer } from "../api/mockServer";
import { QUESTIONS } from "../data/curriculum";
import { Figure } from "../components/Figure";
import { useT } from "../lib/i18n";
import { AppBar, Listen, Progress, Screen } from "./ui";

/** Stable per-question option order, so the right answer isn't always in the same slot. */
function order(qid: string, n: number) {
  let h = 0;
  for (const ch of qid) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  const idx = Array.from({ length: n }, (_, i) => i);
  for (let i = n - 1; i > 0; i--) {
    h = (h * 1103515245 + 12345) >>> 0;
    const j = h % (i + 1);
    [idx[i], idx[j]] = [idx[j], idx[i]];
  }
  return idx;
}

interface Props {
  questions: string[];
  tag: string;
  /** Question id that is a spaced re-check (shown with a subtle label). */
  recheckId?: string;
  submitting?: boolean;
  onSubmit: (answers: Answer[]) => void;
  exitTo: string;
}

export function Quiz({ questions, tag, recheckId, submitting, onSubmit, exitTo }: Props) {
  const { t, tx } = useT();
  const [i, setI] = useState(0);
  const [answers, setAnswers] = useState<Record<string, number | null | undefined>>({});
  const q = QUESTIONS[questions[i]];
  const opts = useMemo(() => order(q.id, q.options.length), [q.id, q.options.length]);
  const chosen = answers[q.id];
  const answered = chosen !== undefined;
  const last = i === questions.length - 1;

  const pick = (v: number | null) => setAnswers((a) => ({ ...a, [q.id]: v }));
  const next = () => {
    if (!answered) return;
    if (last) onSubmit(questions.map((id) => ({ question_id: id, chosen: answers[id] ?? null })));
    else setI(i + 1);
  };

  const readText = tx(q.prompt) + ". " + opts.map((o, k) => `${"ABC"[k]}. ${tx(q.options[o].text)}`).join(". ");

  return (
    <Screen
      bar={<AppBar back={exitTo} title={<span className="bar-tag">{tag}</span>} />}
      footer={
        <button type="button" className="btn btn-primary btn-lg btn-block btn-split" disabled={!answered || submitting} onClick={next}>
          <span>{last ? t("submit") : t("next")}</span>
          <ArrowRight size={20} aria-hidden />
        </button>
      }
    >
      <div className="quiz-top">
        {i > 0 && (
          <button type="button" className="btn btn-ghost btn-sm" onClick={() => setI(i - 1)}>
            ← {t("back")}
          </button>
        )}
        <span className="muted small">{t("q_of", { i: i + 1, n: questions.length })}</span>
      </div>
      <Progress value={i} total={questions.length} label={t("q_of", { i: i + 1, n: questions.length })} />

      <section className="question rise" key={q.id} aria-live="polite">
        {q.id === recheckId && (
          <span className="tag tag-blue">
            <History size={14} aria-hidden /> {t("from_earlier")}
          </span>
        )}
        <div className="q-head">
          <h2 className="q-prompt">{tx(q.prompt)}</h2>
          <Listen id={"q-" + q.id} text={readText} compact />
        </div>
        {q.figure && (
          <div className="q-figure">
            <Figure id={q.figure} closed={q.figureClosed} live={false} />
          </div>
        )}
        <div className="options" role="radiogroup" aria-label={tx(q.prompt)}>
          {opts.map((o, k) => {
            const opt = q.options[o];
            return (
              <button
                key={o}
                type="button"
                role="radio"
                aria-checked={chosen === o}
                className={"option" + (chosen === o ? " selected" : "") + (opt.figure ? " has-fig" : "")}
                onClick={() => pick(o)}
              >
                <span className="opt-letter" aria-hidden>
                  {"ABC"[k]}
                </span>
                {opt.figure ? (
                  <span className="opt-fig">
                    <Figure id={opt.figure} title={`${"ABC"[k]}`} />
                  </span>
                ) : (
                  <span className="opt-text">{tx(opt.text)}</span>
                )}
              </button>
            );
          })}
          <button
            type="button"
            role="radio"
            aria-checked={chosen === null}
            className={"option unsure" + (chosen === null ? " selected" : "")}
            onClick={() => pick(null)}
          >
            <span className="opt-letter" aria-hidden>
              <CircleQuestionMark size={18} />
            </span>
            <span className="opt-text">{t("not_sure")}</span>
          </button>
        </div>
      </section>
    </Screen>
  );
}
