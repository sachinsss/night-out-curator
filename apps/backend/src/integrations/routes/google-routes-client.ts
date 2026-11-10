import { RouteLegSchema, type RouteLeg } from "@night-out/contracts";
import type { Fetcher } from "../http.js";
import { readJson } from "../http.js";
import type { TransitRealtimeClient } from "../transit/transit-realtime-client.js";
import type { RouteOptions, RoutesClient, RouteStop } from "./routes-client.js";

const minutes = (value: unknown) => Number(String(value ?? "0s").replace("s", "")) / 60;
const waypoint = (stop: RouteStop) => ({
  waypoint: { location: { latLng: { latitude: stop.latitude, longitude: stop.longitude } } },
});

export class GoogleRoutesClient implements RoutesClient {
  constructor(
    private readonly apiKey: string,
    private readonly fetcher: Fetcher = fetch,
    private readonly realtime?: TransitRealtimeClient,
  ) {}

  async compute(
    stops: RouteStop[],
    mode: "walking" | "driving" | "rideshare" | "transit",
    options: RouteOptions = {},
  ): Promise<RouteLeg[]> {
    return Promise.all(
      stops.slice(0, -1).map((origin, index) => {
        const destination = stops[index + 1]!;
        return mode === "transit"
          ? this.transitLeg(
              origin,
              destination,
              options.departureTimes?.[index],
              options.transitPreference,
            )
          : this.matrixLeg(origin, destination, mode);
      }),
    );
  }

  private async matrixLeg(
    origin: RouteStop,
    destination: RouteStop,
    mode: "walking" | "driving" | "rideshare",
  ): Promise<RouteLeg> {
    const response = await this.fetcher(
      "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix",
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "X-Goog-Api-Key": this.apiKey,
          "X-Goog-FieldMask":
            "originIndex,destinationIndex,status,condition,distanceMeters,duration",
        },
        body: JSON.stringify({
          origins: [waypoint(origin)],
          destinations: [waypoint(destination)],
          travelMode: mode === "walking" ? "WALK" : "DRIVE",
        }),
        signal: AbortSignal.timeout(10_000),
      },
    );
    const route = ((await readJson(response, "Google Routes")) as Array<Record<string, any>>)[0];
    if (!route || route.condition !== "ROUTE_EXISTS")
      throw new Error("Google Routes returned no route");
    return RouteLegSchema.parse({
      fromPlaceId: origin.placeId,
      toPlaceId: destination.placeId,
      distanceMeters: route.distanceMeters,
      durationMinutes: minutes(route.duration),
      mode: mode === "walking" ? "walking" : "driving",
    });
  }

  private async transitLeg(
    origin: RouteStop,
    destination: RouteStop,
    departureTime?: string,
    preference: "less_walking" | "fewer_transfers" = "less_walking",
  ): Promise<RouteLeg> {
    const response = await this.fetcher(
      "https://routes.googleapis.com/directions/v2:computeRoutes",
      {
        method: "POST",
        headers: {
          "content-type": "application/json",
          "X-Goog-Api-Key": this.apiKey,
          "X-Goog-FieldMask":
            "routes.distanceMeters,routes.duration,routes.legs.steps.travelMode,routes.legs.steps.transitDetails",
        },
        body: JSON.stringify({
          origin: waypoint(origin).waypoint,
          destination: waypoint(destination).waypoint,
          travelMode: "TRANSIT",
          ...(departureTime ? { departureTime } : {}),
          transitPreferences: {
            routingPreference:
              preference === "fewer_transfers" ? "FEWER_TRANSFERS" : "LESS_WALKING",
          },
        }),
        signal: AbortSignal.timeout(12_000),
      },
    );
    const route = (
      (await readJson(response, "Google Transit Routes")) as { routes?: Array<Record<string, any>> }
    ).routes?.[0];
    if (!route) throw new Error("Google Routes returned no public-transit route");
    const steps = (route.legs ?? []).flatMap((leg: any) => leg.steps ?? []);
    const transitSegments = steps
      .filter((step: any) => step.travelMode === "TRANSIT" && step.transitDetails)
      .map((step: any) => {
        const details = step.transitDetails;
        const line = details.transitLine ?? {};
        const stops = details.stopDetails ?? {};
        return {
          routeId: line.nameShort ?? line.name ?? null,
          lineName: line.nameShort ?? line.name ?? line.vehicle?.name?.text ?? "Transit",
          headsign: details.headsign ?? null,
          departureStop: stops.departureStop?.name ?? "Departure stop",
          arrivalStop: stops.arrivalStop?.name ?? "Arrival stop",
          departureTime: stops.departureTime ?? null,
          arrivalTime: stops.arrivalTime ?? null,
          stopCount: details.stopCount ?? null,
          vehicleType: line.vehicle?.type ?? null,
        };
      });
    const routeIds = transitSegments
      .map((segment: { routeId: string | null }) => segment.routeId)
      .filter((value: string | null): value is string => Boolean(value));
    const realtime = this.realtime ? await this.realtime.getStatus(routeIds) : null;
    return RouteLegSchema.parse({
      fromPlaceId: origin.placeId,
      toPlaceId: destination.placeId,
      distanceMeters: route.distanceMeters ?? 0,
      durationMinutes: minutes(route.duration),
      mode: "transit",
      transitSegments,
      realtime,
    });
  }
}
