import { describe, expect, it } from "vitest";
import {
  PlanningOutputSchema,
  RecommendationRequestSchema,
  SearchPlanSchema,
  validatePlanningCandidates,
} from "./recommendation.js";

const validRequest = {
  location: { latitude: 33.4255, longitude: -111.94, label: "Tempe" },
  date: "2026-11-14",
  startTime: "19:00",
  partySize: 2,
  budgetPerPerson: 50,
  currency: "USD" as const,
  preferences: ["cocktails", "vegetarian"],
  excludedCategories: [],
  transportation: "walking" as const,
  stopCount: 2,
};

describe("RecommendationRequestSchema", () => {
  it("accepts a complete recommendation request", () => {
    expect(RecommendationRequestSchema.parse(validRequest)).toEqual(validRequest);
  });

  it("rejects a non-positive budget", () => {
    expect(() =>
      RecommendationRequestSchema.parse({ ...validRequest, budgetPerPerson: 0 }),
    ).toThrow();
  });

  it("accepts public transit preferences", () => {
    expect(
      RecommendationRequestSchema.parse({
        ...validRequest,
        transportation: "transit",
        transitPreference: "fewer_transfers",
      }),
    ).toMatchObject({ transportation: "transit", transitPreference: "fewer_transfers" });
  });

  it("rejects more than four stops", () => {
    expect(() => RecommendationRequestSchema.parse({ ...validRequest, stopCount: 5 })).toThrow();
  });
});

describe("agent contracts", () => {
  it("bounds discovery radius and query count", () => {
    expect(() =>
      SearchPlanSchema.parse({
        queries: Array(6).fill("bar"),
        includedTypes: [],
        excludedTypes: [],
        radiusMeters: 5000,
        priorities: [],
      }),
    ).toThrow();
    expect(() =>
      SearchPlanSchema.parse({
        queries: ["bar"],
        includedTypes: [],
        excludedTypes: [],
        radiusMeters: 50001,
        priorities: [],
      }),
    ).toThrow();
  });

  it("rejects itinerary venue ids outside the candidate set", () => {
    const output = PlanningOutputSchema.parse({
      itineraries: [
        {
          title: "Night",
          summary: "A plan",
          stops: [{ placeId: "unknown", startTime: "19:00", durationMinutes: 60, reason: "Match" }],
        },
      ],
    });
    expect(() => validatePlanningCandidates(output, new Set(["known"]))).toThrow(
      "unknown Place ID",
    );
  });
});
