import { defineConfig } from "vitest/config";

// The store falls back to memory when localStorage is missing, so plain Node is enough.
export default defineConfig({
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
