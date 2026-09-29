import { useEffect, useSyncExternalStore } from "react";
import type { ScreenKey } from "./annotations";

/** Tracks which prototype screen is showing, so the design-notes panel can follow along. */
let current: ScreenKey = "home";
const listeners = new Set<() => void>();

export function useMarkScreen(key: ScreenKey) {
  useEffect(() => {
    current = key;
    listeners.forEach((l) => l());
  }, [key]);
}

export const useCurrentScreen = () =>
  useSyncExternalStore(
    (fn) => {
      listeners.add(fn);
      return () => listeners.delete(fn);
    },
    () => current,
  );
