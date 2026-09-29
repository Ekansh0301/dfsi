import { HashRouter, Navigate, Route, Routes } from "react-router-dom";
import { LearnerApp } from "./learner/LearnerApp";
import { EducatorApp } from "./educator/EducatorApp";
import { Overview } from "./shell/Overview";
import { LearnerFrame } from "./shell/LearnerFrame";
import { SideBySide } from "./shell/SideBySide";
import { FlowMap } from "./shell/FlowMap";
import { TopBar } from "./shell/TopBar";

/** `?embed=1` renders an app bare (used by the side-by-side demo iframes). */
const embedded = new URLSearchParams(window.location.search).has("embed");

export default function App() {
  if (embedded)
    return (
      <HashRouter>
        <div className="embed">
          <Routes>
            <Route path="/learner/*" element={<LearnerApp />} />
            <Route path="/educator/*" element={<EducatorApp />} />
            <Route path="*" element={<Navigate to="/learner" replace />} />
          </Routes>
        </div>
      </HashRouter>
    );

  return (
    <HashRouter>
      <div className="shell">
        <TopBar />
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/learner/*" element={<LearnerFrame />} />
          <Route
            path="/educator/*"
            element={
              <div className="edu-frame">
                <EducatorApp />
              </div>
            }
          />
          <Route path="/demo" element={<SideBySide />} />
          <Route path="/flows" element={<FlowMap />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </div>
    </HashRouter>
  );
}
