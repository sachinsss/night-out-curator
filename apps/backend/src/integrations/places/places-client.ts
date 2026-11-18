import type { Venue } from "@night-out/contracts";

export interface PlaceSearchInput {
  query: string;
  latitude: number;
  longitude: number;
  radiusMeters: number;
}

export interface PlacesClient {
  textSearch(input: PlaceSearchInput): Promise<Venue[]>;
  getDetails(placeId: string): Promise<Venue>;
}
