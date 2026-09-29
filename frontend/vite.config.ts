import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Relative base so the build works from any static host (Netlify drag-and-drop, GitHub Pages, file server).
export default defineConfig({
  base: "./",
  plugins: [react()],
  server: { port: 5173, host: true },
});
