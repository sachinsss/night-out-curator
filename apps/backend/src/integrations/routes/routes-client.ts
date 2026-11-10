import type { RouteLeg } from "@night-out/contracts";
export interface RouteStop {
  placeId: string;
  latitude: number;
  longitude: number;
}
export interface RouteOptions {
  departureTimes?: string[];
  transitPreference?: "less_walking" | "fewer_transfers";
}
export interface RoutesClient {
  compute(
    stops: RouteStop[],
    mode: "walking" | "driving" | "rideshare" | "transit",
    options?: RouteOptions,
  ): Promise<RouteLeg[]>;
}
