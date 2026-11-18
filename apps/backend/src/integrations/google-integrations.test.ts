import { describe, expect, it, vi } from "vitest";
import type { Fetcher } from "./http.js";
import { GooglePlacesClient } from "./places/google-places-client.js";
import { GoogleRoutesClient } from "./routes/google-routes-client.js";
import { GoogleWeatherClient } from "./weather/google-weather-client.js";

const jsonResponse = (body: unknown, status = 200) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });

describe("Google integrations", () => {
  it("normalizes text-search places and drops closed records", async () => {
    const fetcher = vi.fn<Fetcher>(async () =>
      jsonResponse({
        places: [
          {
            id: "open",
            displayName: { text: "Open Place" },
            formattedAddress: "1 Main",
            location: { latitude: 33.4, longitude: -111.9 },
            primaryType: "restaurant",
            businessStatus: "OPERATIONAL",
            rating: 4.5,
            userRatingCount: 20,
          },
          {
            id: "closed",
            displayName: { text: "Closed Place" },
            location: { latitude: 33.4, longitude: -111.9 },
            businessStatus: "CLOSED_PERMANENTLY",
          },
        ],
      }),
    );
    const client = new GooglePlacesClient("key", fetcher);
    const venues = await client.textSearch({
      query: "dinner",
      latitude: 33.4,
      longitude: -111.9,
      radiusMeters: 3000,
    });
    expect(venues).toHaveLength(1);
    expect(venues[0]).toMatchObject({ placeId: "open", name: "Open Place", rating: 4.5 });
    expect(JSON.stringify(fetcher.mock.calls[0]?.[1]?.headers)).not.toContain("authorization");
  });

  it("redacts provider response bodies from errors", async () => {
    const client = new GooglePlacesClient(
      "secret-key",
      async () => new Response("contains-secret-key", { status: 403 }),
    );
    await expect(
      client.textSearch({ query: "dinner", latitude: 33.4, longitude: -111.9, radiusMeters: 3000 }),
    ).rejects.not.toThrow(/secret-key/);
  });

  it("normalizes hourly weather into planning context", async () => {
    const client = new GoogleWeatherClient("key", async () =>
      jsonResponse({
        forecastHours: [
          {
            interval: { startTime: "2026-11-14T19:00:00Z" },
            weatherCondition: { description: { text: "Rain" } },
            precipitation: { probability: { percent: 70 } },
            temperature: { degrees: 60, unit: "FAHRENHEIT" },
          },
        ],
      }),
    );
    const result = await client.getHourly({ latitude: 33.4, longitude: -111.9, hours: 6 });
    expect(result.warnings).toContain("Rain is likely; prefer indoor venues.");
  });

  it("normalizes a route matrix result", async () => {
    const client = new GoogleRoutesClient("key", async () =>
      jsonResponse([
        {
          originIndex: 0,
          destinationIndex: 0,
          condition: "ROUTE_EXISTS",
          distanceMeters: 1600,
          duration: "600s",
        },
      ]),
    );
    const legs = await client.compute(
      [
        { placeId: "a", latitude: 33.4, longitude: -111.9 },
        { placeId: "b", latitude: 33.41, longitude: -111.91 },
      ],
      "walking",
    );
    expect(legs[0]).toMatchObject({
      fromPlaceId: "a",
      toPlaceId: "b",
      distanceMeters: 1600,
      durationMinutes: 10,
      mode: "walking",
    });
  });

  it("normalizes Google public-transit steps and attaches realtime status", async () => {
    const fetcher = vi.fn<Fetcher>(async () =>
      jsonResponse({
        routes: [
          {
            distanceMeters: 2500,
            duration: "1200s",
            legs: [
              {
                steps: [
                  {
                    travelMode: "TRANSIT",
                    transitDetails: {
                      stopDetails: {
                        departureStop: { name: "Mill Ave" },
                        arrivalStop: { name: "Downtown Phoenix" },
                        departureTime: "2026-11-15T02:00:00Z",
                        arrivalTime: "2026-11-15T02:20:00Z",
                      },
                      transitLine: { nameShort: "A", vehicle: { type: "LIGHT_RAIL" } },
                      headsign: "Phoenix",
                      stopCount: 4,
                    },
                  },
                ],
              },
            ],
          },
        ],
      }),
    );
    const realtime = {
      getStatus: vi.fn(async () => ({
        status: "delayed" as const,
        delayMinutes: 5,
        alerts: [],
        checkedAt: "2026-11-09T00:00:00.000Z",
      })),
    };
    const client = new GoogleRoutesClient("key", fetcher, realtime);
    const legs = await client.compute(
      [
        { placeId: "a", latitude: 33.4, longitude: -111.9 },
        { placeId: "b", latitude: 33.41, longitude: -111.91 },
      ],
      "transit",
      { departureTimes: ["2026-11-14T19:00:00-07:00"], transitPreference: "fewer_transfers" },
    );
    expect(legs[0]).toMatchObject({
      mode: "transit",
      durationMinutes: 20,
      transitSegments: [{ lineName: "A", departureStop: "Mill Ave" }],
      realtime: { status: "delayed", delayMinutes: 5 },
    });
    expect(realtime.getStatus).toHaveBeenCalledWith(["A"]);
    expect(JSON.parse(String(fetcher.mock.calls[0]?.[1]?.body))).toMatchObject({
      travelMode: "TRANSIT",
      transitPreferences: { routingPreference: "FEWER_TRANSFERS" },
    });
  });
});
