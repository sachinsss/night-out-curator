import { act, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, afterEach, expect, test, vi } from "vitest";
import { ResultMap } from "./ResultMap";
import { resultFixture } from "./results.test-fixtures";
const mocks = vi.hoisted(() => ({
  load: vi.fn(),
  select: vi.fn(),
  markers: [] as Array<{ click: () => void }>,
  polylines: vi.fn(),
}));
vi.mock("./google-maps-loader", () => ({
  loadGoogleMaps: mocks.load,
  onGoogleMapsAuthFailure: () => () => {},
}));
beforeEach(() => {
  mocks.markers = [];
  mocks.polylines.mockClear();
  class Map {
    fitBounds = vi.fn();
    setMapTypeId = vi.fn();
  }
  class Bounds {
    extend = vi.fn();
  }
  class Marker {
    addListener(_name: string, callback: () => void) {
      mocks.markers.push({ click: callback });
      return { remove: vi.fn() };
    }
    setMap = vi.fn();
  }
  class Polyline {
    constructor(options: unknown) {
      mocks.polylines(options);
    }
    setMap = vi.fn();
  }
  const api = {
    maps: {
      Map,
      LatLngBounds: Bounds,
      Marker,
      Polyline,
      SymbolPath: { CIRCLE: 0 },
      event: { trigger: vi.fn() },
    },
  };
  vi.stubGlobal("google", api);
  mocks.load.mockResolvedValue(api);
});
afterEach(() => vi.unstubAllGlobals());
test("draws only returned road geometry and makes numbered markers selectable", async () => {
  const select = vi.fn();
  render(
    <ResultMap
      itinerary={resultFixture.itineraries[0]!}
      preview={{
        legs: [
          {
            fromPlaceId: "place1",
            toPlaceId: "place2",
            distanceMeters: 100,
            durationMinutes: 2,
            encodedPolyline: "??_ibE_ibE",
          },
        ],
        warnings: [],
      }}
      onSelect={select}
    />,
  );
  await waitFor(() => expect(mocks.markers.length).toBe(3));
  expect(mocks.polylines).toHaveBeenCalledOnce();
  act(() => mocks.markers[1]!.click());
  expect(select).toHaveBeenCalledWith(1);
});
test("keeps stop markers without drawing fabricated straight routes", async () => {
  render(<ResultMap itinerary={resultFixture.itineraries[0]!} preview={null} onSelect={vi.fn()} />);
  await waitFor(() => expect(mocks.markers.length).toBe(3));
  expect(mocks.polylines).not.toHaveBeenCalled();
});
test("shows a recoverable error when Google Maps fails", async () => {
  mocks.load.mockRejectedValue(new Error("Network unavailable"));
  render(<ResultMap itinerary={resultFixture.itineraries[0]!} preview={null} onSelect={vi.fn()} />);
  expect(await screen.findByRole("alert")).toHaveTextContent("could not load");
  expect(screen.getByRole("button", { name: "Retry map" })).toBeVisible();
});
