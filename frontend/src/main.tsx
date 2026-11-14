import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "@fontsource/ibm-plex-sans/400.css";
import "@fontsource/ibm-plex-sans/500.css";
import "@fontsource/ibm-plex-sans/600.css";
import "@fontsource/ibm-plex-sans-devanagari/400.css";
import "@fontsource/ibm-plex-sans-devanagari/600.css";
import "@fontsource/space-grotesk/500.css";
import "@fontsource/space-grotesk/700.css";
import "./styles/tokens.css";
import "./styles/base.css";
import "./styles/learner.css";
import "./styles/educator.css";
import "./styles/shell.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);

// Offline support (public/sw.js): only in the built site, so development always loads fresh files.
if (import.meta.env.PROD && "serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker
      .register("./sw.js")
      .then(() => navigator.serviceWorker.ready)
      .then((reg) => {
        const loaded = performance.getEntriesByType("resource").map((e) => e.name);
        reg.active?.postMessage({ cache: [location.href.split("#")[0], ...loaded] });
      })
      .catch(() => {
        /* not supported here (for example a file:// page): the app works online as before */
      });
  });
}
