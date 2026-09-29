import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, Check, Droplets, Lock, SunMedium, Zap } from "lucide-react";
import { finishOnboarding, setLang, type Answer } from "../api/mockServer";
import type { Lang, LearnerState } from "../api/types";
import { MODULES, PLACEMENT, moduleById } from "../data/curriculum";
import { useT } from "../lib/i18n";
import { useMe } from "../lib/store";
import { useMarkScreen } from "../shell/screenStore";
import { Quiz } from "./Quiz";
import { AppBar, Listen, Screen } from "./ui";

export function Welcome() {
  useMarkScreen("welcome");
  const { t, lang } = useT();
  const nav = useNavigate();
  const langs: { id: Lang; label: string; sub: string }[] = [
    { id: "hi", label: "हिंदी", sub: "Hindi" },
    { id: "en", label: "English", sub: "अंग्रेज़ी" },
  ];
  return (
    <Screen
      bar={<AppBar right={<span />} />}
      footer={
        <button type="button" className="btn btn-primary btn-lg btn-block btn-split" onClick={() => nav("/learner/setup/track")}>
          <span>{t("continue")}</span>
          <ArrowRight size={20} aria-hidden />
        </button>
      }
    >
      <div className="hero-illus rise" aria-hidden>
        <WelcomeArt />
      </div>
      <h1 className="display rise-2">{t("welcome_title")}</h1>
      <p className="lead rise-2">{t("welcome_body")}</p>
      <Listen id="welcome" text={t("welcome_title") + " " + t("welcome_body")} />
      <fieldset className="choice-group rise-3">
        <legend className="label">{t("choose_lang")}</legend>
        <div className="lang-grid">
          {langs.map((l) => (
            <button
              key={l.id}
              type="button"
              className={"choice lang-choice" + (lang === l.id ? " selected" : "")}
              aria-pressed={lang === l.id}
              onClick={() => setLang(l.id)}
              lang={l.id}
            >
              <span className="choice-title">{l.label}</span>
              <span className="choice-sub" lang={l.id === "hi" ? "en" : "hi"}>
                {l.sub}
              </span>
              {lang === l.id && <Check className="choice-check" size={20} aria-hidden />}
            </button>
          ))}
        </div>
      </fieldset>
    </Screen>
  );
}

export function TrackSelect() {
  useMarkScreen("track");
  const { t } = useT();
  const nav = useNavigate();
  return (
    <Screen
      bar={<AppBar back="/learner/welcome" />}
      footer={
        <button type="button" className="btn btn-primary btn-lg btn-block btn-split" onClick={() => nav("/learner/setup/experience")}>
          <span>{t("continue")}</span>
          <ArrowRight size={20} aria-hidden />
        </button>
      }
    >
      <p className="eyebrow">1 / 3</p>
      <h1 className="title">{t("track_title")}</h1>
      <div className="stack-12">
        <button type="button" className="choice track selected" aria-pressed>
          <span className="track-icon amber">
            <Zap size={26} aria-hidden />
          </span>
          <span>
            <span className="choice-title">{t("track_electrical")}</span>
            <span className="choice-sub">{t("track_electrical_sub")}</span>
          </span>
          <Check className="choice-check" size={20} aria-hidden />
        </button>
        {[
          { icon: SunMedium, label: t("track_solar") },
          { icon: Droplets, label: t("track_plumbing") },
        ].map(({ icon: Icon, label }) => (
          <div key={label} className="choice track disabled" aria-disabled>
            <span className="track-icon">
              <Icon size={26} aria-hidden />
            </span>
            <span>
              <span className="choice-title">{label}</span>
              <span className="choice-sub">{t("coming_soon")}</span>
            </span>
            <Lock size={18} className="choice-check" aria-hidden />
          </div>
        ))}
      </div>
    </Screen>
  );
}

export function ExperienceSelect({ onPick }: { onPick: (e: LearnerState["experience"]) => void }) {
  useMarkScreen("experience");
  const { t } = useT();
  const nav = useNavigate();
  const [exp, setExp] = useState<LearnerState["experience"]>();
  const opts: { id: NonNullable<LearnerState["experience"]>; label: string; level: number }[] = [
    { id: "new", label: t("exp_new"), level: 1 },
    { id: "some", label: t("exp_some"), level: 2 },
    { id: "experienced", label: t("exp_experienced"), level: 3 },
  ];
  return (
    <Screen
      bar={<AppBar back="/learner/setup/track" />}
      footer={
        <button
          type="button"
          className="btn btn-primary btn-lg btn-block btn-split"
          disabled={!exp}
          onClick={() => {
            onPick(exp);
            nav("/learner/placement");
          }}
        >
          <span>{t("continue")}</span>
          <ArrowRight size={20} aria-hidden />
        </button>
      }
    >
      <p className="eyebrow">2 / 3</p>
      <h1 className="title">{t("exp_title")}</h1>
      <div className="stack-12" role="radiogroup" aria-label={t("exp_title")}>
        {opts.map((o) => (
          <button
            key={o.id}
            type="button"
            role="radio"
            aria-checked={exp === o.id}
            className={"choice track" + (exp === o.id ? " selected" : "")}
            onClick={() => setExp(o.id)}
          >
            <span className="level-bars" aria-hidden>
              {[1, 2, 3].map((b) => (
                <span key={b} className={b <= o.level ? "on" : ""} style={{ height: 8 + b * 6 }} />
              ))}
            </span>
            <span className="choice-title">{o.label}</span>
            {exp === o.id && <Check className="choice-check" size={20} aria-hidden />}
          </button>
        ))}
      </div>
    </Screen>
  );
}

export function Placement({ experience }: { experience: LearnerState["experience"] }) {
  useMarkScreen("placement");
  const { t } = useT();
  const nav = useNavigate();
  const [started, setStarted] = useState(false);
  const [busy, setBusy] = useState(false);

  const submit = async (answers: Answer[]) => {
    setBusy(true);
    await finishOnboarding(experience ?? "some", answers);
    nav("/learner/start", { replace: true });
  };

  if (busy)
    return (
      <Screen bar={<AppBar right={<span />} />}>
        <div className="center-fill" role="status">
          <div className="spinner" />
          <p className="lead">{t("finding_start")}</p>
        </div>
      </Screen>
    );

  if (!started)
    return (
      <Screen
        bar={<AppBar back="/learner/setup/experience" />}
        footer={
          <button type="button" className="btn btn-primary btn-lg btn-block btn-split" onClick={() => setStarted(true)}>
            <span>{t("start")}</span>
            <ArrowRight size={20} aria-hidden />
          </button>
        }
      >
        <p className="eyebrow">3 / 3</p>
        <h1 className="title">{t("placement_title")}</h1>
        <p className="lead">{t("placement_body")}</p>
        <Listen id="placement" text={t("placement_title") + ". " + t("placement_body")} />
        <div className="placement-art" aria-hidden>
          {PLACEMENT.map((_, i) => (
            <span key={i} style={{ animationDelay: `${i * 60}ms` }} />
          ))}
        </div>
      </Screen>
    );

  return <Quiz questions={PLACEMENT} tag={t("placement_title")} onSubmit={submit} exitTo="/learner/setup/experience" submitting={busy} />;
}

export function StartingPoint() {
  useMarkScreen("start");
  const { t, tx, lang } = useT();
  const nav = useNavigate();
  const me = useMe();
  const m = moduleById(me.currentModule);
  const skipped = MODULES.filter((x) => x.number < m.number);
  const names = skipped.map((s) => tx(s.title));
  const joined = names.length > 1 ? names.slice(0, -1).join(", ") + (lang === "hi" ? " और " : " and ") + names[names.length - 1] : names[0];
  const reason = skipped.length ? t("start_reason_skip", { x: joined }) : t("start_reason_first");
  return (
    <Screen
      bar={<AppBar right={<span />} />}
      footer={
        <button type="button" className="btn btn-primary btn-lg btn-block btn-split" onClick={() => nav(`/learner/quiz/${m.id}`)}>
          <span>{t("begin_module", { n: m.number })}</span>
          <ArrowRight size={20} aria-hidden />
        </button>
      }
    >
      <div className="rec-card rise">
        <span className="tag">{t("rec_label")}</span>
        <p className="muted">{t("start_title")}</p>
        <h1 className="rec-title">
          {t("module_n", { n: m.number })} · {tx(m.title)}
        </h1>
        <p className="lead">{reason}</p>
        <Listen id="start" text={`${t("start_title")} ${tx(m.title)}. ${reason}`} />
      </div>
      <ol className="mini-path rise-2" aria-label={t("progress_title")}>
        {MODULES.map((x) => (
          <li key={x.id} className={x.number < m.number ? "done" : x.id === m.id ? "now" : ""}>
            <span className="dot">{x.number < m.number ? <Check size={14} aria-hidden /> : x.number}</span>
            <span className="mp-label">{tx(x.title)}</span>
          </li>
        ))}
      </ol>
    </Screen>
  );
}

function WelcomeArt() {
  return (
    <svg viewBox="0 0 320 150" width="100%" height="150">
      <defs>
        <pattern id="wg" width="16" height="16" patternUnits="userSpaceOnUse">
          <path d="M16 0H0V16" fill="none" stroke="var(--grid)" strokeWidth="1" />
        </pattern>
      </defs>
      <rect width="320" height="150" rx="20" fill="var(--surface-2)" />
      <rect width="320" height="150" rx="20" fill="url(#wg)" />
      <g fill="none" stroke="var(--wire)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        <path d="M40 68V40h90" />
        <path d="M170 40h110v70H40V82" />
        <circle cx="130" cy="40" r="4" fill="var(--wire)" />
        <line x1="130" y1="40" x2="170" y2="40" />
        <circle cx="170" cy="40" r="4" fill="var(--wire)" />
        <path className="welcome-flow" d="M40 110V40h240v70H40" stroke="var(--wire-live)" strokeDasharray="3 14" />
      </g>
      <circle cx="280" cy="75" r="26" fill="var(--amber)" opacity="0.28" />
      <circle cx="280" cy="75" r="17" fill="var(--surface)" stroke="var(--wire)" strokeWidth="3" />
      <path d="M269 64l22 22M291 64l-22 22" stroke="var(--wire)" strokeWidth="3" strokeLinecap="round" />
      <g stroke="var(--wire)" strokeWidth="3" strokeLinecap="round">
        <line x1="24" y1="68" x2="56" y2="68" strokeWidth="3.5" />
        <line x1="32" y1="82" x2="48" y2="82" strokeWidth="5" />
      </g>
    </svg>
  );
}
