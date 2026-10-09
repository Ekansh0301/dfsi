import { useState } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import type { LearnerState } from "../api/types";
import { useMe } from "../lib/store";
import { Home, ModuleQuiz, Recommendation, Results } from "./Loop";
import { ExperienceSelect, Placement, StartingPoint, TrackSelect, Welcome } from "./Onboarding";
import { Messages, ProgressScreen } from "./Path";
import { GotIt, HelpSent, Learn, Stuck } from "./Remedial";

/** Learner app: mobile-first, one primary action per screen. */
export function LearnerApp() {
  const me = useMe();
  const [experience, setExperience] = useState<LearnerState["experience"]>("some");
  const entry = me.onboarded ? "/learner/home" : "/learner/welcome";
  return (
    <div className="learner-app">
      <Routes>
        <Route index element={<Navigate to={entry} replace />} />
        <Route path="welcome" element={<Welcome />} />
        <Route path="setup/track" element={<TrackSelect />} />
        <Route path="setup/experience" element={<ExperienceSelect onPick={setExperience} />} />
        <Route path="placement" element={<Placement experience={experience} />} />
        <Route path="start" element={<StartingPoint />} />
        <Route path="home" element={me.onboarded ? <Home /> : <Navigate to="/learner/welcome" replace />} />
        <Route path="quiz/:moduleId" element={<ModuleQuiz />} />
        <Route path="results" element={<Results />} />
        <Route path="next" element={<Recommendation />} />
        <Route path="learn/:contentId" element={<Learn />} />
        <Route path="got-it" element={<GotIt />} />
        <Route path="stuck" element={<Stuck />} />
        <Route path="help-sent" element={<HelpSent />} />
        <Route path="progress" element={<ProgressScreen />} />
        <Route path="messages" element={<Messages />} />
        <Route path="*" element={<Navigate to={entry} replace />} />
      </Routes>
    </div>
  );
}
