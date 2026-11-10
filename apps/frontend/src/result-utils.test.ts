import { expect, test } from "vitest";
import { schedule, mapsLink, decodePolyline } from "./result-utils";
import { requestFixture, resultFixture } from "./results.test-fixtures";
test("computes end times and departures across midnight in Phoenix", () => {
  const stop = resultFixture.itineraries[0]!.stops[0]!;
  const times = schedule(
    [
      { ...stop, startTime: "23:30", durationMinutes: 90 },
      { ...stop, startTime: "01:15", durationMinutes: 45 },
    ],
    "2026-11-14",
  );
  expect(times[0]!.label).toBe("11:30 PM - 1:00 AM");
  expect(times[1]!.start).toBe(1515);
  expect(times[0]!.departureTime).toBe("2026-11-15T08:00:00.000Z");
});
test("preserves stop order and transportation in Maps links", () => {
  const url = new URL(mapsLink(resultFixture.itineraries[0]!.stops, requestFixture));
  expect(url.searchParams.get("origin_place_id")).toBe("place1");
  expect(url.searchParams.get("waypoint_place_ids")).toBe("place2");
  expect(url.searchParams.get("destination_place_id")).toBe("place3");
  expect(url.searchParams.get("travelmode")).toBe("driving");
});
test("decodes provider geometry and rejects truncated polylines", () => {
  expect(decodePolyline("??_ibE_ibE")).toEqual([
    { lat: 0, lng: 0 },
    { lat: 1, lng: 1 },
  ]);
  expect(() => decodePolyline("_")).toThrow();
});
