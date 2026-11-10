import { describe, expect, it, vi } from "vitest";
import { buildApp } from "../app.js";
import { GoogleResultPresentation } from "./google-result-presentation.js";
import type { ResultPresentationService } from "./google-result-presentation.js";
import type { RoutePreviewRequest } from "@night-out/contracts";
const place = {
  placeId: "place1",
  displayCategory: null,
  summary: null,
  websiteUri: null,
  mapsUri: null,
  reviewsUri: null,
  menuUri: null,
  reservable: null,
  parking: [],
  photos: [],
};
const preview: RoutePreviewRequest = {
  stops: [
    { placeId: "one", latitude: 33.4, longitude: -112, departureTime: "2026-11-15T03:30:00.000Z" },
    { placeId: "two", latitude: 33.5, longitude: -112, departureTime: "2026-11-15T05:00:00.000Z" },
  ],
  transportation: "driving",
};
const service = (): ResultPresentationService => ({
  place: vi.fn(async () => place),
  photo: vi.fn(async () => "https://lh3.googleusercontent.com/photo"),
  routes: vi.fn(async () => ({ legs: [], warnings: [] })),
});
const create = (presentation = service()) =>
  buildApp({ workflow: { run: vi.fn() }, presentation, enableDevRoutes: false });
describe("result presentation endpoints", () => {
  it("returns fresh metadata with no-store and handles missing photos", async () => {
    const app = create();
    const response = await app.inject({ url: "/api/v1/places/place1/presentation" });
    expect(response.statusCode).toBe(200);
    expect(response.json().photos).toEqual([]);
    expect(response.headers["cache-control"]).toBe("no-store");
    await app.close();
  });
  it("validates photo resources and widths before contacting Google", async () => {
    const presentation = service();
    const app = create(presentation);
    for (const query of [
      "name=https://evil.example/photo",
      "name=places/a/photos/../secret",
      "name=places/a/photos/b&width=9999",
    ]) {
      expect((await app.inject({ url: `/api/v1/place-photos?${query}` })).statusCode).toBe(400);
    }
    expect(presentation.photo).not.toHaveBeenCalled();
    await app.close();
  });
  it("redirects to temporary media without exposing the server credential", async () => {
    const app = create();
    const response = await app.inject({
      url: "/api/v1/place-photos?name=places/a/photos/b&width=640",
    });
    expect(response.statusCode).toBe(302);
    expect(response.headers.location).toBe("https://lh3.googleusercontent.com/photo");
    expect(response.headers["cache-control"]).toBe("no-store");
    await app.close();
  });
  it("returns a safe retryable failure without upstream secret details", async () => {
    const presentation = service();
    presentation.place = vi.fn(async () => {
      throw new Error("server-secret-key");
    });
    const app = create(presentation);
    const response = await app.inject({ url: "/api/v1/places/place1/presentation" });
    expect(response.statusCode).toBe(502);
    expect(response.body).not.toContain("server-secret");
    await app.close();
  });
  it("validates preview requests and does not save geometry", async () => {
    const presentation = service();
    const app = create(presentation);
    expect(
      (
        await app.inject({
          method: "POST",
          url: "/api/v1/routes/preview",
          payload: { ...preview, stops: [] },
        })
      ).statusCode,
    ).toBe(400);
    const response = await app.inject({
      method: "POST",
      url: "/api/v1/routes/preview",
      payload: preview,
    });
    expect(response.statusCode).toBe(200);
    expect(response.headers["cache-control"]).toBe("no-store");
    expect(presentation.routes).toHaveBeenCalledOnce();
    await app.close();
  });
});
describe("Google result presentation", () => {
  it("normalizes only known presentation fields and photo authors", async () => {
    const fetcher = vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            id: "place1",
            primaryTypeDisplayName: { text: "Mexican Restaurant" },
            photos: [
              {
                name: "places/place1/photos/ref",
                authorAttributions: [
                  { displayName: "Author", uri: "https://maps.google.com/author" },
                ],
              },
            ],
            parkingOptions: { paidStreetParking: true, freeParkingLot: false },
            reservable: true,
            websiteUri: "javascript:alert(1)",
          }),
        ),
    );
    const data = await new GoogleResultPresentation("secret", fetcher).place("place1");
    expect(data.photos[0]?.authors[0]?.name).toBe("Author");
    expect(data.parking).toEqual(["Paid street parking"]);
    expect(data.websiteUri).toBeNull();
    expect(JSON.stringify(data)).not.toContain("secret");
  });
  it("resolves media with a server header and rejects unsafe redirects", async () => {
    const fetcher = vi.fn(
      async () => new Response(JSON.stringify({ photoUri: "https://evil.example/image" })),
    );
    await expect(
      new GoogleResultPresentation("secret", fetcher).photo("places/p/photos/ref", 640),
    ).rejects.toThrow("Photo unavailable");
    expect(fetcher.mock.calls[0]?.length).toBeGreaterThan(0);
  });
  it("returns road geometry and uses TRANSIT preferences for public transit", async () => {
    const fetcher = vi.fn(async (_url: unknown, init?: RequestInit) => {
      const body = JSON.parse(String(init?.body));
      expect(body.travelMode).toBe("TRANSIT");
      expect(body.transitPreferences.routingPreference).toBe("FEWER_TRANSFERS");
      return new Response(
        JSON.stringify({
          routes: [
            { distanceMeters: 3200, duration: "720s", polyline: { encodedPolyline: "encoded" } },
          ],
        }),
      );
    });
    const result = await new GoogleResultPresentation("secret", fetcher).routes({
      ...preview,
      transportation: "transit",
      transitPreference: "fewer_transfers",
    });
    expect(result.legs[0]?.durationMinutes).toBe(12);
    expect(result.legs[0]?.encodedPolyline).toBe("encoded");
  });
  it("handles one stop without API calls and reports failed legs", async () => {
    const fetcher = vi.fn(async () => new Response("{}", { status: 503 }));
    const client = new GoogleResultPresentation("secret", fetcher);
    expect(await client.routes({ ...preview, stops: preview.stops.slice(0, 1) })).toEqual({
      legs: [],
      warnings: [],
    });
    expect(fetcher).not.toHaveBeenCalled();
    expect((await client.routes(preview)).warnings).toHaveLength(1);
  });
});
