import { useEffect, useMemo, useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { ArrowRight, BookOpenCheck, Check, ChevronDown, CircleCheckBig, Clock3, Hand, MessageCircle, Sparkles, Trophy, X } from "lucide-react";
import { getDB, quizFor, submitQuiz, type Answer, type QuizResult } from "../api/mockServer";
import type { ContentItem } from "../api/types";
import { CONCEPTS, MODULES, QUESTIONS, moduleById } from "../data/curriculum";
import { CONTENT } from "../data/content";
import { EDUCATOR } from "../data/seed";
import { useT } from "../lib/i18n";
import { useDB, useMe } from "../lib/store";
import { useMarkScreen } from "../shell/screenStore";
import { Quiz } from "./Quiz";
import { AppBar, Screen } from "./ui";

// ─── H · Home ────────────────────────────────────────────────────────────────
export function Home() {
  useMarkScreen("home");
  const { t, tx } = useT();
  const me = useMe();
  const waiting = useDB((d) => d.escalations.find((e) => e.learner_id === me.id && e.status === "open"));
  const unread = useDB((d) => d.messages.filter((m) => m.learner_id === me.id && !m.read));
  const rec = me.recommendation;
  const m = moduleById(me.currentModule);
  const allDone = MODULES.every((x) => me.completedModules.includes(x.id));
  const doneCount = me.completedModules.length;

  return (
    <Screen nav>
      <div className="home-head">
        <h1 className="title">{t("hello", { name: me.name.split(" ")[0] })}</h1>
        <p className="muted">
          {t("track_electrical")} · {t("module_n", { n: m.number })}
        </p>
      </div>

      {unread.length > 0 && (
        <Link to="/learner/messages" className="banner banner-blue">
          <MessageCircle size={20} aria-hidden />
          <span>{t("new_message", { trainer: unread[0].from })}</span>
          <span className="banner-cta">{t("read")} →</span>
        </Link>
      )}

      <p className="label">{t("your_next_step")}</p>
      {rec ? (
        <RecSummary />
      ) : allDone ? (
        <div className="next-card done">
          <Trophy size={32} aria-hidden />
          <h2>{t("all_done")}</h2>
        </div>
      ) : (
        <div className="next-card">
          <div className="nc-top">
            <span className="tag tag-plain">{t("module_n", { n: m.number })}</span>
            <span className="muted small">
              <Clock3 size={14} aria-hidden /> {t("questions_min", { q: m.quiz.length, m: m.minutes })}
            </span>
          </div>
          <h2 className="nc-title">{tx(m.title)}</h2>
          <p className="muted">{t("home_card_body")}</p>
          <Link to={`/learner/quiz/${m.id}`} className="btn btn-primary btn-lg btn-block btn-split">
            <span>{t("start_check")}</span>
            <ArrowRight size={20} aria-hidden />
          </Link>
        </div>
      )}

      {waiting && (
        <div className="waiting-card" role="status">
          <span className="wc-icon">
            <Hand size={20} aria-hidden />
          </span>
          <div>
            <p className="wc-title">{t("waiting_title", { trainer: EDUCATOR.name })}</p>
            <p className="muted small">{t("waiting_body", { c: tx(CONCEPTS[waiting.concept_id].name) })}</p>
          </div>
        </div>
      )}

      <Link to="/learner/progress" className="path-strip" aria-label={t("progress_title")}>
        <div className="ps-dots">
          {MODULES.map((x) => (
            <span key={x.id} className={me.completedModules.includes(x.id) ? "on" : x.id === me.currentModule ? "cur" : ""} />
          ))}
        </div>
        <span className="small">
          {t("progress_title")} · {doneCount}/{MODULES.length}
        </span>
        <ArrowRight size={16} aria-hidden />
      </Link>
    </Screen>
  );
}

function RecSummary() {
  const { t, tx } = useT();
  const me = useMe();
  const rec = me.recommendation!;
  const item = CONTENT[rec.recommended_content_id];
  return (
    <div className="next-card rec">
      <span className={"tag" + (rec.from_trainer ? " tag-blue" : "")}>{rec.from_trainer ? t("rec_from_trainer") : t("rec_label")}</span>
      <h2 className="nc-title">{tx(rec.diagnostic_text)}</h2>
      <Link to={`/learner/learn/${item.id}`} className="btn btn-primary btn-lg btn-block btn-split">
        <span>{t("start_x", { title: tx(item.title) })}</span>
        <span className="hint">{t("min", { m: item.minutes })}</span>
      </Link>
    </div>
  );
}

// ─── S1 · Assessment ─────────────────────────────────────────────────────────
export function ModuleQuiz() {
  useMarkScreen("quiz");
  const { moduleId = "m1" } = useParams();
  const { t, tx } = useT();
  const nav = useNavigate();
  const m = moduleById(moduleId);
  // Freeze the question list (incl. any interleaved re-check) when the quiz opens.
  const { questions, recheck } = useMemo(() => quizFor(getDB(), moduleId), [moduleId]);
  const recheckId = recheck ? questions[1] : undefined;
  const [busy, setBusy] = useState(false);

  const submit = async (answers: Answer[]) => {
    setBusy(true);
    const result = await submitQuiz(moduleId, answers);
    nav("/learner/results", { state: { result, moduleId }, replace: true });
  };

  return (
    <Quiz
      questions={questions}
      recheckId={recheckId}
      tag={`${t("module_n", { n: m.number })} · ${tx(m.title)}`}
      onSubmit={submit}
      submitting={busy}
      exitTo="/learner/home"
    />
  );
}

// ─── S2 · Results & transition ───────────────────────────────────────────────
export function Results() {
  useMarkScreen("results");
  const { t, tx } = useT();
  const me = useMe();
  const nav = useNavigate();
  const loc = useLocation() as { state?: { result?: QuizResult; moduleId?: string } };
  const [analysing, setAnalysing] = useState(!!loc.state?.result);
  const [showAnswers, setShowAnswers] = useState(false);

  useEffect(() => {
    if (!analysing) return;
    const id = setTimeout(() => setAnalysing(false), 1100);
    return () => clearTimeout(id);
  }, [analysing]);

  const last = me.lastQuiz;
  if (!last) return <Navigate to="/learner/home" replace />;
  const m = moduleById(last.module_id);
  const scored = last.answers.filter((a) => m.quiz.includes(a.question_id));
  const correct = scored.filter((a) => a.correct).length;
  const result = loc.state?.result;
  const rec = me.recommendation;
  const recheck = result?.recheck;
  const next = MODULES.find((x) => !me.completedModules.includes(x.id));

  if (analysing)
    return (
      <Screen bar={<AppBar right={<span />} />}>
        <div className="center-fill" role="status">
          <p className="lead">{t("analysing")}</p>
        </div>
      </Screen>
    );

  const perfect = correct === scored.length;
  const body = rec ? (recheck && !recheck.passed && perfect ? t("results_recheck_gap") : t("results_gap")) : t("results_clean");
  const heading = rec && !perfect ? t("results_great", { n: m.number }) : t("results_clean_title", { n: m.number });
  return (
    <Screen
      bar={<AppBar back="/learner/home" />}
      footer={
        rec ? (
          <button type="button" className="btn btn-primary btn-lg btn-block btn-split" onClick={() => nav("/learner/next")}>
            <span>{t("see_next")}</span>
            <ArrowRight size={20} aria-hidden />
          </button>
        ) : next ? (
          <button type="button" className="btn btn-primary btn-lg btn-block btn-split" onClick={() => nav("/learner/home")}>
            <span>{t("continue_module", { n: next.number })}</span>
            <ArrowRight size={20} aria-hidden />
          </button>
        ) : (
          <Link to="/learner/home" className="btn btn-primary btn-lg btn-block">
            {t("nav_home")}
          </Link>
        )
      }
    >
      <div className="result-hero">
        <div className={"result-badge" + (rec ? "" : " clean")} aria-hidden>
          {rec ? <Sparkles size={34} /> : <CircleCheckBig size={34} />}
        </div>
        <span className="tag tag-plain">
          {t("module_n", { n: m.number })} · {tx(m.title)}
        </span>
        <h1 className="title">{heading}</h1>
        <p className="lead">{body}</p>
      </div>

      <div className="score-row" aria-label={t("results_score", { c: correct, t: scored.length })}>
        <div className="score-dots">
          {scored.map((a) => (
            <span key={a.question_id} className={a.correct ? "ok" : "miss"}>
              {a.correct ? <Check size={14} aria-hidden /> : <X size={14} aria-hidden />}
            </span>
          ))}
        </div>
        <span className="small muted">{t("results_score", { c: correct, t: scored.length })}</span>
      </div>

      {recheck && (
        <div className={"banner " + (recheck.passed ? "banner-teal" : "banner-rust")} role="status">
          {recheck.passed ? <BookOpenCheck size={20} aria-hidden /> : <Clock3 size={20} aria-hidden />}
          <span>
            {recheck.passed
              ? t("recheck_pass", { c: tx(CONCEPTS[recheck.concept].name) })
              : t("recheck_fail", { c: tx(CONCEPTS[recheck.concept].name) })}
          </span>
        </div>
      )}

      <button type="button" className="disclosure" aria-expanded={showAnswers} onClick={() => setShowAnswers(!showAnswers)}>
        <span>{showAnswers ? t("hide_answers") : t("review_answers")}</span>
        <ChevronDown size={18} aria-hidden />
      </button>
      {showAnswers && (
        <ul className="answer-list">
          {last.answers.map((a) => {
            const q = QUESTIONS[a.question_id];
            return (
              <li key={a.question_id} className={a.correct ? "ok" : "miss"}>
                <span className="al-icon" aria-hidden>
                  {a.correct ? <Check size={14} /> : <X size={14} />}
                </span>
                <div>
                  <p className="al-q">{tx(q.prompt)}</p>
                  {!a.correct && (
                    <p className="small muted">
                      {a.chosen === null ? t("you_unsure") : `${t("you_chose")}: ${tx(q.options[a.chosen].text)}`} · {t("correct_answer")}:{" "}
                      <strong>{tx(q.options[q.correct].text)}</strong>
                    </p>
                  )}
                  <p className="small">{tx(q.why)}</p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </Screen>
  );
}

// ─── S3 · Recommendation card ────────────────────────────────────────────────
export function KindIcon({ kind, size = 18 }: { kind: ContentItem["kind"]; size?: number }) {
  if (kind === "practice") return <Hand size={size} aria-hidden />;
  return <BookOpenCheck size={size} aria-hidden />;
}

export function Recommendation() {
  useMarkScreen("next");
  const { t, tx, lang } = useT();
  const me = useMe();
  const nav = useNavigate();
  const [why, setWhy] = useState(false);
  const rec = me.recommendation;
  if (!rec) return <Navigate to="/learner/home" replace />;
  const item = CONTENT[rec.recommended_content_id];
  const observed = tx(CONCEPTS[rec.observed_concept_id].name);
  const target = tx(CONCEPTS[rec.concept_id].name);
  // English concept names are lower-cased mid-sentence; Hindi has no case.
  const mid = (x: string) => (lang === "en" ? x.charAt(0).toLowerCase() + x.slice(1) : x);
  const whyText = rec.from_trainer
    ? t("why_trainer")
    : rec.repeat_gap
      ? t("why_repeat")
      : rec.chain.length > 1
        ? t("why_chain", { A: observed, a: mid(observed), b: mid(target) })
        : t("why_direct", { a: mid(target) });

  return (
    <Screen
      bar={<AppBar back="/learner/home" />}
      footer={
        <button type="button" className="btn btn-primary btn-lg btn-block btn-split" onClick={() => nav(`/learner/learn/${item.id}`)}>
          <span>{t("start_x", { title: tx(item.title) })}</span>
          <span className="hint">{t("min", { m: item.minutes })}</span>
        </button>
      }
    >
      <article className="rec-card" aria-labelledby="rec-diag">
        <div className="rec-tags">
          <span className={"tag" + (rec.from_trainer ? " tag-blue" : "")}>{rec.from_trainer ? t("rec_from_trainer") : t("rec_label")}</span>
          {rec.repeat_gap && <span className="tag tag-rust">{t("repeat_gap")}</span>}
        </div>
        <h1 id="rec-diag" className="rec-title">
          {tx(rec.diagnostic_text)}
        </h1>

        <div className="prescription">
          <span className={"rx-icon kind-" + item.kind}>
            <KindIcon kind={item.kind} size={22} />
          </span>
          <div className="rx-body">
            <p className="rx-title">{tx(item.title)}</p>
            <p className="small muted">
              {t(("kind_" + item.kind) as "kind_walkthrough")} · {t("min", { m: item.minutes })}
            </p>
          </div>
        </div>

        <button type="button" className="disclosure" aria-expanded={why} onClick={() => setWhy(!why)}>
          <span>{t("why_this")}</span>
          <ChevronDown size={18} aria-hidden />
        </button>
        {why && (
          <div className="why-box">
            {rec.chain.length > 1 && !rec.from_trainer && (
              <ol className="chain">
                <li className="chain-node root">
                  <span className="chain-k">{t("why_start")}</span>
                  {target}
                </li>
                <li className="chain-node">
                  <span className="chain-k">{t("why_then")}</span>
                  {observed}
                </li>
              </ol>
            )}
            <p className="small">{whyText}</p>
          </div>
        )}
      </article>
    </Screen>
  );
}
