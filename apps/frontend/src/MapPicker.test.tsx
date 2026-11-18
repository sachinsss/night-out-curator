import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MapPicker } from "./MapPicker";

const loadGoogleMaps = vi.hoisted(() => vi.fn());
const onGoogleMapsAuthFailure = vi.hoisted(() => vi.fn(() => vi.fn()));
vi.mock("./google-maps-loader", () => ({
  loadGoogleMaps,
  onGoogleMapsAuthFailure,
  GoogleMapsLoadError: class GoogleMapsLoadError extends Error {},
}));

const panTo = vi.fn();

function mapsApi() {
  class FakeMap {
    constructor(_host: HTMLElement, _options: google.maps.MapOptions) {}
    panTo = panTo;
    getCenter() {
      return { lat: () => 33.425, lng: () => -111.94 };
    }
  }
  return { maps: { Map: FakeMap } } as unknown as typeof google;
}

describe("MapPicker", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.stubEnv("VITE_GOOGLE_MAPS_API_KEY", "browser-key");
    vi.stubEnv("VITE_GOOGLE_MAPS_MAP_ID", "");
    loadGoogleMaps.mockResolvedValue(mapsApi());
  });

  it("shows an actionable error when the browser key is missing", async () => {
    vi.stubEnv("VITE_GOOGLE_MAPS_API_KEY", "");
    loadGoogleMaps.mockRejectedValue(
      new Error(
        "Google Maps is not configured. Add VITE_GOOGLE_MAPS_API_KEY and restart the frontend.",
      ),
    );
    render(<MapPicker value={{ lat: 33.4484, lng: -112.074 }} onChange={vi.fn()} />);
    expect(await screen.findByRole("alert")).toHaveTextContent("VITE_GOOGLE_MAPS_API_KEY");
  });

  it("commits the map center only after confirmation and closes the picker", async () => {
    const onChange = vi.fn();
    const onClose = vi.fn();
    render(
      <MapPicker value={{ lat: 33.4484, lng: -112.074 }} onChange={onChange} onClose={onClose} />,
    );
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Use this location" })).toBeEnabled(),
    );
    expect(onChange).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Use this location" }));
    expect(onChange).toHaveBeenCalledExactlyOnceWith({ lat: 33.425, lng: -111.94 });
    expect(onClose).toHaveBeenCalledOnce();
  });

  it("synchronizes external coordinate changes without recreating the map", async () => {
    const { rerender } = render(
      <MapPicker value={{ lat: 33.4484, lng: -112.074 }} onChange={vi.fn()} />,
    );
    await waitFor(() => expect(loadGoogleMaps).toHaveBeenCalledTimes(1));
    rerender(<MapPicker value={{ lat: 33.42, lng: -111.93 }} onChange={vi.fn()} />);
    expect(panTo).toHaveBeenLastCalledWith({ lat: 33.42, lng: -111.93 });
    expect(loadGoogleMaps).toHaveBeenCalledTimes(1);
  });

  it("uses the latest coordinates when they change while Google Maps is loading", async () => {
    let resolveMaps!: (api: typeof google) => void;
    loadGoogleMaps.mockReturnValue(
      new Promise((resolve) => {
        resolveMaps = resolve;
      }),
    );
    const { rerender } = render(
      <MapPicker value={{ lat: 33.4484, lng: -112.074 }} onChange={vi.fn()} />,
    );
    rerender(<MapPicker value={{ lat: 33.42, lng: -111.93 }} onChange={vi.fn()} />);
    await act(async () => resolveMaps(mapsApi()));
    expect(panTo).toHaveBeenLastCalledWith({ lat: 33.42, lng: -111.93 });
  });
});
