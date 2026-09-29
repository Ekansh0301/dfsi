import { useSyncExternalStore } from "react";
import { getDB, subscribe } from "../api/mockServer";
import type { DB } from "../api/types";

/** Subscribe a component to the mock backend state. */
export function useDB<T = DB>(select: (d: DB) => T = (d) => d as unknown as T): T {
  return select(useSyncExternalStore(subscribe, getDB, getDB));
}

export const useMe = () => useDB((d) => d.learners[d.activeLearnerId]);
