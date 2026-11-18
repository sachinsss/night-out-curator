import { describe, expect, it, vi } from "vitest";
import type { RecommendationRequest, SearchPlan, Venue } from "@night-out/contracts";
import { RecommendationWorkflow } from "./recommendation-workflow.js";

const request: RecommendationRequest = {
  location: { latitude: 33.4255, longitude: -111.94, label: "Tempe" },
  date: "2026-11-14",
  startTime: "19:00",
  partySize: 2,
  budgetPerPerson: 50,
  currency: "USD",
  preferences: ["cocktails"],
  excludedCategories: [],
  transportation: "walking",
  stopCount: 1,
};
const venue: Venue = {
  placeId: "place-1",
  name: "Venue",
  category: "bar",
  address: "1 Main",
  location: { latitude: 33.42, longitude: -111.94 },
  businessStatus: "OPERATIONAL",
  priceLevel: "PRICE_LEVEL_MODERATE",
  rating: 4.5,
  userRatingCount: 100,
  regularOpeningHours: null,
  mapsUri: "https://maps.google.com",
  retrievedAt: "2026-11-09T00:00:00.000Z",
  distanceMeters: 100,
  relevanceScore: 0.8,
  warnings: [],
};
const searchPlan: SearchPlan = {
  queries: ["cocktail bars"],
  includedTypes: ["bar"],
  excludedTypes: [],
  radiusMeters: 3000,
  priorities: ["cocktails"],
};

function dependencies(planningPlaceId = "place-1") {
  return {
    discoveryAgent: { run: vi.fn(async () => searchPlan) },
    planningAgent: {
      run: vi.fn(async () => ({
        itineraries: [
          {
            title: "Night",
            summary: "Plan",
            stops: [
              {
                placeId: planningPlaceId,
                startTime: "19:00",
                durationMinutes: 90,
                reason: "Match",
              },
            ],
          },
        ],
      })),
    },
    places: { textSearch: vi.fn(async () => [venue]), getDetails: vi.fn(async () => venue) },
    weather: {
      getHourly: vi.fn(async () => ({
        summary: "Clear",
        warnings: [],
        retrievedAt: new Date().toISOString(),
      })),
    },
    routes: { compute: vi.fn(async () => []) },
  };
}

describe("RecommendationWorkflow", () => {
  it("runs discovery and weather concurrently", async () => {
    let releaseDiscovery!: () => void;
    let releaseWeather!: () => void;
    const discoveryGate = new Promise<void>((resolve) => {
      releaseDiscovery = resolve;
    });
    const weatherGate = new Promise<void>((resolve) => {
      releaseWeather = resolve;
    });
    const deps = dependencies();
    deps.discoveryAgent.run = vi.fn(async () => {
      await discoveryGate;
      return searchPlan;
    });
    deps.weather.getHourly = vi.fn(async () => {
      await weatherGate;
      return { summary: "Clear", warnings: [], retrievedAt: new Date().toISOString() };
    });
    const running = new RecommendationWorkflow(deps).run(request);
    await vi.waitFor(() => {
      expect(deps.discoveryAgent.run).toHaveBeenCalledOnce();
      expect(deps.weather.getHourly).toHaveBeenCalledOnce();
    });
    releaseDiscovery();
    releaseWeather();
    expect((await running).status).toBe("valid");
  });

  it("rejects unknown Place IDs and performs only one repair", async () => {
    const deps = dependencies("unknown");
    const result = await new RecommendationWorkflow(deps).run(request);
    expect(deps.planningAgent.run).toHaveBeenCalledTimes(2);
    expect(result.status).toBe("unresolved");
    expect(result.itineraries).toEqual([]);
  });

  it("returns a stable itinerary containing verified venue data", async () => {
    const result = await new RecommendationWorkflow(dependencies()).run(request);
    expect(result.itineraries[0]?.stops[0]?.venue.placeId).toBe("place-1");
    expect(result.cache).toEqual({ discoveryHit: false, planningHit: false });
  });
});

it("marks incomplete travel verification provisional for multi-stop plans", async () => {
  const deps = dependencies();
  const second = { ...venue, placeId: "place-2", name: "Second venue" };
  deps.places.textSearch = vi.fn(async () => [venue, second]);
  deps.planningAgent.run = vi.fn(async () => ({
    itineraries: [
      {
        title: "Night",
        summary: "Plan",
        stops: [
          { placeId: "place-1", startTime: "19:00", durationMinutes: 90, reason: "Dinner" },
          { placeId: "place-2", startTime: "21:00", durationMinutes: 60, reason: "Drinks" },
        ],
      },
    ],
  }));
  const result = await new RecommendationWorkflow(deps).run({
    ...request,
    stopCount: 2,
    budgetPerPerson: 125,
  });
  expect(result.status).toBe("provisional");
  expect(result.warnings.join(" ")).toContain("Travel routes could not be verified");
});
