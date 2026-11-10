import { useEffect, useRef, useState } from "react";
import type { PlacePresentation } from "@night-out/contracts";
import { fetchPlacePresentation } from "./presentation-api";
export type VenuePresentationState = { loading: boolean; data?: PlacePresentation; error?: string };
export function useVenuePresentation(ids: string[]) {
  const [states, setStates] = useState<Record<string, VenuePresentationState>>({});
  const pending = useRef(new Map<string, Promise<PlacePresentation>>());
  const mounted = useRef(false);
  function load(id: string, retry = false) {
    if (retry) pending.current.delete(id);
    let promise = pending.current.get(id);
    if (!promise) {
      promise = fetchPlacePresentation(id);
      pending.current.set(id, promise);
    }
    setStates((current) => ({ ...current, [id]: { loading: true } }));
    promise
      .then((data) => {
        if (mounted.current)
          setStates((current) => ({ ...current, [id]: { loading: false, data } }));
      })
      .catch(() => {
        if (mounted.current)
          setStates((current) => ({
            ...current,
            [id]: { loading: false, error: "Venue information could not load." },
          }));
      });
  }
  const identity = [...new Set(ids)].join("|");
  useEffect(() => {
    mounted.current = true;
    identity
      .split("|")
      .filter(Boolean)
      .forEach((id) => load(id));
    return () => {
      mounted.current = false;
    };
  }, [identity]);
  return { states, retry: (id: string) => load(id, true) };
}
