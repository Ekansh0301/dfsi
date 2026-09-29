import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, ArrowRight, CalendarClock, CircleCheckBig, Eye, Hand, Pause, Play, RotateCcw, Send, ThumbsUp, WifiOff } from "lucide-react";
import { gotIt, startContent, stuck } from "../api/mockServer";
import type { ConceptId, StuckReason } from "../api/types";
import { CONCEPTS } from "../data/curriculum";
import { CONTENT } from "../data/content";
import { EDUCATOR } from "../data/seed";
import { Figure } from "../components/Figure";
import { speak, stopSpeaking } from "../lib/speech";
import { useT } from "../lib/i18n";
import { useMe } from "../lib/store";
import { useMarkScreen } from "../shell/screenStore";
import { KindIcon } from "./Loop";
import { AppBar, Listen, Progress, Screen } from "./ui";

// ─── S4 · Remedial view ──────────────────────────────────────────────────────
export function Learn() {
  useMarkScreen("learn");
  const { contentId = "" } = useParams();
  const item = CONTENT[contentId];
  const { t, tx, lang } = useT();
  const nav = useNavigate();
  const [i, setI] = useState(0);
  const [revealed, setRevealed] = useState<Record<number, boolean>>({});
  const [playing, setPlaying] = useState(false);
  const [busy, setBusy] = useState(false);
  const timer = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (item) startContent(item.id, item.concept);
  }, [item]);
  useEffect(
    () => () => {
      stopSpeaking();
      window.clearTimeout(timer.current);
    },
    [],
  );

  // Narrated items auto-advance, step by step, while playing.
  const stepText = item ? tx(item.steps[i].text) : "";
  useEffect(() => {
    if (!item || item.kind !== "video" || !playing) return;
    // Hold each step long enough to read, even if speech ends early or is unavailable.
    const started = Date.now();
    const minDwell = Math.max(2500, stepText.length * 60);
    const advance = () => {
      timer.current = window.setTimeout(
        () => {
          if (i < item.steps.length - 1) setI((x) => x + 1);
          else setPlaying(false);
        },
        Math.max(700, minDwell - (Date.now() - started)),
      );
    };
    speak("video-" + item.id + i, stepText, lang, advance);
    return () => window.clearTimeout(timer.current);
  }, [item, i, playing, lang, stepText]);

  if (!item) return <Navigate to="/learner/home" replace />;
  const step = item.steps[i];
  const fig = step.figure ?? item.figure;
  const last = i === item.steps.length - 1;
  const needsReveal = !!step.answer && !revealed[i];
  const atEnd = last && !needsReveal;

  const onGotIt = async () => {
    setBusy(true);
    stopSpeaking();
    await gotIt();
    nav("/learner/got-it", { replace: true, state: { concept: item.concept } });
  };
  const onStuck = () => {
    stopSpeaking();
    nav("/learner/stuck", { state: { concept: item.concept } });
  };

  return (
    <Screen
      bar={
        <AppBar
          back="/learner/next"
          title={
            <span className="bar-tag">
              <KindIcon kind={item.kind} size={14} /> {t(("kind_" + item.kind) as "kind_walkthrough")}
            </span>
          }
          right={
            !atEnd ? (
              <button type="button" className="btn btn-ghost btn-sm stuck-link" onClick={onStuck}>
                <Hand size={16} aria-hidden /> {t("still_stuck")}
              </button>
            ) : (
              <span />
            )
          }
        />
      }
      footer={
        atEnd ? (
          <div className="feedback-bar">
            <p className="label center">{t("feedback_q")}</p>
            <div className="fb-buttons">
              <button type="button" className="btn btn-success btn-lg" onClick={onGotIt} disabled={busy}>
                <ThumbsUp size={20} aria-hidden /> {t("got_it")}
              </button>
              <button type="button" className="btn btn-danger-outline btn-lg" onClick={onStuck} disabled={busy}>
                <Hand size={20} aria-hidden /> {t("still_stuck")}
              </button>
            </div>
          </div>
        ) : (
          <div className="step-nav">
            <button type="button" className="btn btn-secondary btn-lg" onClick={() => setI(i - 1)} disabled={i === 0} aria-label={t("back")}>
              <ArrowLeft size={20} aria-hidden />
            </button>
            {needsReveal ? (
              <button type="button" className="btn btn-primary btn-lg grow" onClick={() => setRevealed({ ...revealed, [i]: true })}>
                <Eye size={20} aria-hidden /> {t("show_answer")}
              </button>
            ) : (
              <button type="button" className="btn btn-primary btn-lg grow btn-split" onClick={() => setI(i + 1)}>
                <span>{t("next")}</span>
                <ArrowRight size={20} aria-hidden />
              </button>
            )}
          </div>
        )
      }
    >
      <div className="lesson-head">
        <h1 className="title-sm">{tx(item.title)}</h1>
        <p className="small muted">
          {t("min", { m: item.minutes })} ·{" "}
          {item.offline ? (
            <span className="offline-pill">
              <WifiOff size={12} aria-hidden /> {t("offline_ok")}
            </span>
          ) : (
            t("needs_data")
          )}
        </p>
      </div>
      <Progress value={i} total={item.steps.length} label={t("step_of", { i: i + 1, n: item.steps.length })} />

      <section className="lesson-stage" key={i} aria-live="polite">
        {fig && (
          <div className={"lesson-figure rise" + (item.kind === "video" ? " video" : "")}>
            <Figure id={fig} highlight={step.highlight} closed={step.closed} />
            {item.kind === "video" && (
              <button
                type="button"
                className="video-ctl"
                onClick={() => {
                  if (playing) {
                    stopSpeaking();
                    setPlaying(false);
                  } else {
                    if (last) setI(0);
                    setPlaying(true);
                  }
                }}
              >
                {playing ? <Pause size={20} aria-hidden /> : last ? <RotateCcw size={20} aria-hidden /> : <Play size={20} aria-hidden />}
                <span>{playing ? t("pause") : last ? t("replay") : t("play")}</span>
              </button>
            )}
          </div>
        )}
        <p className="step-count small muted">{t("step_of", { i: i + 1, n: item.steps.length })}</p>
        <p className="step-text rise-2">{tx(step.text)}</p>
        {item.kind !== "video" && (
          <Listen id={`step-${item.id}-${i}`} text={tx(step.text) + (step.answer && revealed[i] ? " " + tx(step.answer) : "")} />
        )}
        {step.answer && revealed[i] && (
          <div className="answer-reveal rise">
            <CircleCheckBig size={18} aria-hidden />
            <p>{tx(step.answer)}</p>
          </div>
        )}
      </section>
    </Screen>
  );
}

// ─── S4a · Got it ────────────────────────────────────────────────────────────
export function GotIt() {
  useMarkScreen("gotit");
  const { t, tx } = useT();
  const loc = useLocation();
  const concept = (loc.state as { concept?: ConceptId } | null)?.concept ?? "diagrams";
  return (
    <Screen
      bar={<AppBar right={<span />} />}
      footer={
        <Link to="/learner/home" className="btn btn-primary btn-lg btn-block btn-split">
          <span>{t("continue_learning")}</span>
          <ArrowRight size={20} aria-hidden />
        </Link>
      }
    >
      <div className="center-block">
        <div className="big-badge teal rise" aria-hidden>
          <ThumbsUp size={40} />
        </div>
        <h1 className="title rise-2">{t("gotit_title")}</h1>
        <p className="lead rise-2">{t("gotit_body", { c: tx(CONCEPTS[concept].name) })}</p>
        <Listen id="gotit" text={t("gotit_title") + " " + t("gotit_body", { c: tx(CONCEPTS[concept].name) })} />
      </div>
    </Screen>
  );
}

// ─── S5 · Still stuck ────────────────────────────────────────────────────────
export function Stuck() {
  useMarkScreen("stuck");
  const { t } = useT();
  const nav = useNavigate();
  const me = useMe();
  const [reason, setReason] = useState<StuckReason>();
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  if (!me.recommendation) return <Navigate to="/learner/home" replace />;

  const reasons: { id: StuckReason; label: string }[] = [
    { id: "unclear", label: t("reason_unclear") },
    { id: "need_example", label: t("reason_need_example") },
    { id: "language", label: t("reason_language") },
    { id: "other", label: t("reason_other") },
  ];
  const send = async () => {
    setBusy(true);
    await stuck(reason ?? "other", note.trim());
    nav("/learner/help-sent", { replace: true });
  };
  return (
    <Screen
      bar={<AppBar back={-1} />}
      footer={
        <button type="button" className="btn btn-primary btn-lg btn-block btn-split" onClick={send} disabled={busy}>
          <span>{busy ? t("sending") : t("send_trainer")}</span>
          <Send size={20} aria-hidden />
        </button>
      }
    >
      <div className="big-badge rust small-badge" aria-hidden>
        <Hand size={28} />
      </div>
      <h1 className="title">{t("stuck_title")}</h1>
      <p className="lead">{t("stuck_body")}</p>
      <div className="reason-grid" role="radiogroup" aria-label={t("stuck_title")}>
        {reasons.map((r) => (
          <button
            key={r.id}
            type="button"
            role="radio"
            aria-checked={reason === r.id}
            className={"choice reason" + (reason === r.id ? " selected" : "")}
            onClick={() => setReason(r.id)}
          >
            {r.label}
          </button>
        ))}
      </div>
      <label className="sr-only" htmlFor="stuck-note">
        {t("note_placeholder")}
      </label>
      <textarea
        id="stuck-note"
        className="textarea"
        rows={3}
        placeholder={t("note_placeholder")}
        value={note}
        onChange={(e) => setNote(e.target.value)}
      />
    </Screen>
  );
}

// ─── S5b · Help sent ─────────────────────────────────────────────────────────
export function HelpSent() {
  useMarkScreen("helpsent");
  const { t, lang } = useT();
  return (
    <Screen
      bar={<AppBar right={<span />} />}
      footer={
        <Link to="/learner/home" className="btn btn-primary btn-lg btn-block btn-split">
          <span>{t("continue_learning")}</span>
          <ArrowRight size={20} aria-hidden />
        </Link>
      }
    >
      <div className="center-block">
        <div className="big-badge blue rise" aria-hidden>
          <Send size={36} />
        </div>
        <h1 className="title rise-2">{t("help_sent_title", { trainer: EDUCATOR.name })}</h1>
        <p className="lead rise-2">{t("help_sent_body")}</p>
        <Listen id="helpsent" text={t("help_sent_title", { trainer: EDUCATOR.name }) + " " + t("help_sent_body")} />
        <div className="trainer-chip rise-3">
          <span className="avatar">KM</span>
          <strong>{EDUCATOR.name}</strong>
          <span className="small muted tc-eta">
            <CalendarClock size={13} aria-hidden /> {lang === "hi" ? "~1 दिन" : "~1 day"}
          </span>
        </div>
      </div>
    </Screen>
  );
}
