import GtfsRealtimeBindings from "gtfs-realtime-bindings";
import { describe, expect, it } from "vitest";
import { ValleyMetroRealtimeClient } from "./valley-metro-realtime-client.js";

function feed() {
  const message = GtfsRealtimeBindings.transit_realtime.FeedMessage.create({
    header: { gtfsRealtimeVersion: "2.0" },
    entity: [
      {
        id: "trip",
        tripUpdate: { trip: { routeId: "A" }, stopTimeUpdate: [{ departure: { delay: 360 } }] },
      },
      {
        id: "alert",
        alert: {
          informedEntity: [{ routeId: "A" }],
          headerText: { translation: [{ text: "Rail platform changed", language: "en" }] },
        },
      },
    ],
  });
  return GtfsRealtimeBindings.transit_realtime.FeedMessage.encode(message).finish();
}

describe("ValleyMetroRealtimeClient", () => {
  it("matches delays and alerts to a selected route", async () => {
    const bytes = feed();
    const body = bytes.buffer.slice(
      bytes.byteOffset,
      bytes.byteOffset + bytes.byteLength,
    ) as ArrayBuffer;
    const client = new ValleyMetroRealtimeClient(
      ["https://example.test/feed"],
      async () => new Response(body),
    );
    await expect(client.getStatus(["A"])).resolves.toMatchObject({
      status: "alert",
      delayMinutes: 6,
      alerts: ["Rail platform changed"],
    });
  });
  it("returns an explicit unavailable result when feeds are not configured", async () => {
    await expect(new ValleyMetroRealtimeClient([]).getStatus(["A"])).resolves.toMatchObject({
      status: "unavailable",
    });
  });
});
