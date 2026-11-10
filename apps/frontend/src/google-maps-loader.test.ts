import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

beforeEach(() => vi.resetModules());

afterEach(() => {
  document.querySelectorAll("script[data-nightline-google-maps]").forEach((node) => node.remove());
  delete (window as Window & { google?: unknown }).google;
  vi.restoreAllMocks();
});

describe("loadGoogleMaps", () => {
  it("rejects a blank browser key without adding a script", async () => {
    const { GoogleMapsLoadError, loadGoogleMaps } = await import("./google-maps-loader");
    await expect(loadGoogleMaps("  ")).rejects.toBeInstanceOf(GoogleMapsLoadError);
    expect(document.querySelector("script[data-nightline-google-maps]")).toBeNull();
  });

  it("shares one script and promise across concurrent loads", () => {
    return import("./google-maps-loader").then(({ loadGoogleMaps }) => {
      const first = loadGoogleMaps("browser-key");
      const second = loadGoogleMaps("browser-key");
      expect(second).toBe(first);
      expect(document.querySelectorAll("script[data-nightline-google-maps]")).toHaveLength(1);
    });
  });

  it("rejects a failed script and permits a later retry", async () => {
    const { loadGoogleMaps } = await import("./google-maps-loader");
    const first = loadGoogleMaps("browser-key");
    const script = document.querySelector<HTMLScriptElement>("script[data-nightline-google-maps]")!;
    script.onerror?.(new Event("error"));
    await expect(first).rejects.toThrow("could not be loaded");
    loadGoogleMaps("browser-key");
    expect(document.querySelectorAll("script[data-nightline-google-maps]")).toHaveLength(1);
  });

  it("uses an already loaded Google Maps API without injecting a script", async () => {
    const { loadGoogleMaps } = await import("./google-maps-loader");
    const loaded = { maps: { Map: class {} } };
    (window as Window & { google?: unknown }).google = loaded;
    await expect(loadGoogleMaps("browser-key")).resolves.toBe(loaded);
    expect(document.querySelector("script[data-nightline-google-maps]")).toBeNull();
  });

  it("notifies subscribers when Google reports an authentication failure", async () => {
    const { loadGoogleMaps, onGoogleMapsAuthFailure } = await import("./google-maps-loader");
    const listener = vi.fn();
    onGoogleMapsAuthFailure(listener);
    const promise = loadGoogleMaps("browser-key");
    (window as Window & { google?: unknown }).google = { maps: { Map: class {} } };
    (window as unknown as Record<string, (() => void) | undefined>).__nightlineGoogleMapsReady!();
    (window as unknown as Record<string, (() => void) | undefined>).gm_authFailure!();
    await promise;
    expect(listener).toHaveBeenCalledWith(
      expect.objectContaining({ message: expect.stringContaining("authentication") }),
    );
  });
});
