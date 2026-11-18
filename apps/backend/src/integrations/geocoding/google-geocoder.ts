import type { Fetcher } from "../http.js";
import { readJson } from "../http.js";
import type { Geocoder, ResolvedLocation } from "./geocoder.js";

export class GoogleGeocoder implements Geocoder {
  constructor(
    private readonly apiKey: string,
    private readonly fetcher: Fetcher = fetch,
  ) {}
  async resolve(query: string): Promise<ResolvedLocation> {
    const url = new URL("https://maps.googleapis.com/maps/api/geocode/json");
    url.searchParams.set("address", query);
    url.searchParams.set("key", this.apiKey);
    const response = await this.fetcher(url, { signal: AbortSignal.timeout(10_000) });
    const data = (await readJson(response, "Google Geocoding")) as {
      status?: string;
      results?: Array<{
        formatted_address: string;
        geometry: { location: { lat: number; lng: number } };
      }>;
    };
    const first = data.results?.[0];
    if (!first || data.status !== "OK") throw new Error("Location could not be resolved");
    return {
      label: first.formatted_address,
      latitude: first.geometry.location.lat,
      longitude: first.geometry.location.lng,
    };
  }
}
