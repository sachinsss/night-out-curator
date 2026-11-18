import { expect, it, vi } from "vitest";
import type { RecommendationRequest, SearchPlan, Venue } from "@night-out/contracts";
import { RecommendationWorkflow } from "./recommendation-workflow.js";

it("reuses cached discovery and planning outputs without invoking agents", async () => {
  const request: RecommendationRequest = {
    location: { latitude: 33.4, longitude: -111.9, label: "Tempe" },
    date: "2026-11-14",
    startTime: "19:00",
    partySize: 2,
    budgetPerPerson: 50,
    currency: "USD",
    preferences: ["bar"],
    excludedCategories: [],
    transportation: "walking",
    stopCount: 1,
  };
  const plan: SearchPlan = {
    queries: ["bars"],
    includedTypes: ["bar"],
    excludedTypes: [],
    radiusMeters: 3000,
    priorities: [],
  };
  const venue: Venue = {
    placeId: "p1",
    name: "Bar",
    category: "bar",
    address: "",
    location: { latitude: 33.4, longitude: -111.9 },
    businessStatus: "OPERATIONAL",
    priceLevel: "PRICE_LEVEL_MODERATE",
    rating: 4,
    userRatingCount: 10,
    regularOpeningHours: {},
    mapsUri: null,
    retrievedAt: "2026-11-09T00:00:00.000Z",
    distanceMeters: 0,
    relevanceScore: 0.8,
    warnings: [],
  };
  const planning = {
    itineraries: [
      {
        title: "Night",
        summary: "Plan",
        stops: [{ placeId: "p1", startTime: "19:00", durationMinutes: 60, reason: "Match" }],
      },
    ],
  };
  const values: Record<string, unknown> = { discovery: plan, planning };
  const cache = {
    createKey: (parts: { agent: string }) => parts.agent,
    get: <T>(key: string): T | null => (values[key] as T | undefined) ?? null,
    set: (_key: string, _value: unknown, _ttl: number) => undefined,
  };
  const discoveryAgent = { run: vi.fn() };
  const planningAgent = { run: vi.fn() };
  const workflow = new RecommendationWorkflow({
    discoveryAgent,
    planningAgent,
    cache,
    cacheIdentities: {
      discovery: { provider: "test", model: "a" },
      planning: { provider: "test", model: "b" },
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
  });
  const result = await workflow.run(request);
  expect(discoveryAgent.run).not.toHaveBeenCalled();
  expect(planningAgent.run).not.toHaveBeenCalled();
  expect(result.cache).toEqual({ discoveryHit: true, planningHit: true });
});
