import { VenueSchema, type Venue } from "@night-out/contracts";
import type { Fetcher } from "../http.js";
import { readJson } from "../http.js";
import type { PlaceSearchInput, PlacesClient } from "./places-client.js";

const SEARCH_FIELDS =
  "places.id,places.displayName,places.formattedAddress,places.location,places.primaryType,places.businessStatus,places.regularOpeningHours,places.priceLevel,places.rating,places.userRatingCount,places.googleMapsUri";
const DETAIL_FIELDS = SEARCH_FIELDS.replaceAll("places.", "");

type GooglePlace = Record<string, any>;

function normalize(place: GooglePlace, retrievedAt: string): Venue | null {
  if (
    !place.id ||
    !place.displayName?.text ||
    place.location?.latitude == null ||
    place.location?.longitude == null
  )
    return null;
  if (["CLOSED_PERMANENTLY", "CLOSED_TEMPORARILY"].includes(place.businessStatus)) return null;
  return VenueSchema.parse({
    placeId: place.id,
    name: place.displayName.text,
    category: place.primaryType ?? "place",
    address: place.formattedAddress ?? "",
    location: place.location,
    businessStatus: place.businessStatus ?? null,
    priceLevel: place.priceLevel ?? null,
    rating: place.rating ?? null,
    userRatingCount: place.userRatingCount ?? null,
    regularOpeningHours: place.regularOpeningHours ?? null,
    mapsUri: place.googleMapsUri ?? null,
    retrievedAt,
    distanceMeters: null,
    relevanceScore: 0,
    warnings: [
      ...(place.priceLevel ? [] : ["Price information is unavailable."]),
      ...(place.regularOpeningHours ? [] : ["Opening hours are unavailable."]),
    ],
  });
}

export class GooglePlacesClient implements PlacesClient {
  constructor(
    private readonly apiKey: string,
    private readonly fetcher: Fetcher = fetch,
  ) {}

  async textSearch(input: PlaceSearchInput): Promise<Venue[]> {
    const response = await this.fetcher("https://places.googleapis.com/v1/places:searchText", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "X-Goog-Api-Key": this.apiKey,
        "X-Goog-FieldMask": SEARCH_FIELDS,
      },
      body: JSON.stringify({
        textQuery: input.query,
        pageSize: 20,
        locationBias: {
          circle: {
            center: { latitude: input.latitude, longitude: input.longitude },
            radius: input.radiusMeters,
          },
        },
      }),
      signal: AbortSignal.timeout(15_000),
    });
    const data = (await readJson(response, "Google Places")) as { places?: GooglePlace[] };
    const retrievedAt = new Date().toISOString();
    return (data.places ?? [])
      .map((place) => normalize(place, retrievedAt))
      .filter((venue): venue is Venue => venue !== null);
  }

  async getDetails(placeId: string): Promise<Venue> {
    const response = await this.fetcher(
      `https://places.googleapis.com/v1/places/${encodeURIComponent(placeId)}`,
      {
        headers: { "X-Goog-Api-Key": this.apiKey, "X-Goog-FieldMask": DETAIL_FIELDS },
        signal: AbortSignal.timeout(15_000),
      },
    );
    const venue = normalize(
      (await readJson(response, "Google Places")) as GooglePlace,
      new Date().toISOString(),
    );
    if (!venue) throw new Error("Google Places returned an unusable place record");
    return venue;
  }
}
