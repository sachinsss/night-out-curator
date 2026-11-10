import { describe, expect, it, vi } from "vitest";
import type { RecommendationRequest, RecommendationResponse } from "@night-out/contracts";
import { buildApp } from "./app.js";

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
const response: RecommendationResponse = {
  requestId: "28af4c86-4fa9-4fba-b7cf-4d7862ee768f",
  status: "unresolved",
  itineraries: [],
  weather: null,
  warnings: ["No matches"],
  generatedAt: "2026-11-09T00:00:00.000Z",
  cache: { discoveryHit: false, planningHit: false },
};

describe("Fastify API", () => {
  it("reports health without revealing credentials", async () => {
    const app = buildApp({
      workflow: { run: vi.fn(async () => response) },
      enableDevRoutes: false,
    });
    const result = await app.inject({ method: "GET", url: "/api/v1/health" });
    expect(result.statusCode).toBe(200);
    expect(result.json()).toMatchObject({ status: "ok", agents: 2 });
    expect(result.body).not.toMatch(/api.?key|secret/i);
    await app.close();
  });

  it("creates and retrieves a recommendation", async () => {
    const app = buildApp({
      workflow: { run: vi.fn(async () => response) },
      enableDevRoutes: false,
    });
    const created = await app.inject({
      method: "POST",
      url: "/api/v1/recommendations",
      payload: request,
    });
    expect(created.statusCode).toBe(200);
    const found = await app.inject({
      method: "GET",
      url: `/api/v1/recommendations/${response.requestId}`,
    });
    expect(found.statusCode).toBe(200);
    expect(found.json()).toEqual(response);
    await app.close();
  });

  it("returns 400 for an invalid request", async () => {
    const app = buildApp({
      workflow: { run: vi.fn(async () => response) },
      enableDevRoutes: false,
    });
    const result = await app.inject({
      method: "POST",
      url: "/api/v1/recommendations",
      payload: { ...request, budgetPerPerson: 0 },
    });
    expect(result.statusCode).toBe(400);
    await app.close();
  });

  it("does not register development routes when disabled", async () => {
    const app = buildApp({
      workflow: { run: vi.fn(async () => response) },
      enableDevRoutes: false,
    });
    expect((await app.inject({ method: "GET", url: "/api/dev/health" })).statusCode).toBe(404);
    await app.close();
  });
});
