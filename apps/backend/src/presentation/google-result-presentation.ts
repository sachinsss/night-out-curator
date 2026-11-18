import {
  PlacePresentationSchema,
  RoutePreviewSchema,
  type PlacePresentation,
  type RoutePreview,
  type RoutePreviewRequest,
} from "@night-out/contracts";
import { readJson, type Fetcher } from "../integrations/http.js";

export interface ResultPresentationService {
  place(placeId: string): Promise<PlacePresentation>;
  photo(name: string, width: number): Promise<string>;
  routes(input: RoutePreviewRequest): Promise<RoutePreview>;
}
const safeUrl = (value: unknown): string | null => {
  try {
    const url = new URL(String(value));
    return url.protocol === "https:" ? url.href : null;
  } catch {
    return null;
  }
};
const PARKING: Record<string, string> = {
  freeParkingLot: "Free parking lot",
  paidParkingLot: "Paid parking lot",
  freeStreetParking: "Free street parking",
  paidStreetParking: "Paid street parking",
  valetParking: "Valet parking",
  freeGarageParking: "Free garage parking",
  paidGarageParking: "Paid garage parking",
};
export class GoogleResultPresentation implements ResultPresentationService {
  constructor(
    private readonly key: string,
    private readonly fetcher: Fetcher = fetch,
  ) {}
  async place(placeId: string): Promise<PlacePresentation> {
    const response = await this.fetcher(
      `https://places.googleapis.com/v1/places/${encodeURIComponent(placeId)}`,
      {
        headers: {
          "X-Goog-Api-Key": this.key,
          "X-Goog-FieldMask":
            "id,primaryTypeDisplayName,editorialSummary,websiteUri,googleMapsUri,googleMapsLinks,photos,reservable,parkingOptions",
        },
        signal: AbortSignal.timeout(12000),
      },
    );
    const place = (await readJson(response, "Place presentation")) as Record<string, any>;
    return PlacePresentationSchema.parse({
      placeId,
      displayCategory: place.primaryTypeDisplayName?.text ?? null,
      summary: place.editorialSummary?.text ?? null,
      websiteUri: safeUrl(place.websiteUri),
      mapsUri: safeUrl(place.googleMapsUri),
      reviewsUri: safeUrl(place.googleMapsLinks?.reviewsUri),
      menuUri: null,
      reservable: typeof place.reservable === "boolean" ? place.reservable : null,
      parking: Object.entries(PARKING)
        .filter(([key]) => place.parkingOptions?.[key] === true)
        .map(([, label]) => label),
      photos: (place.photos ?? []).slice(0, 3).map((photo: any) => ({
        name: photo.name,
        sourceUri: safeUrl(photo.googleMapsUri),
        authors: (photo.authorAttributions ?? []).map((author: any) => ({
          name: author.displayName ?? "Photo contributor",
          uri: safeUrl(author.uri),
        })),
      })),
    });
  }
  async photo(name: string, width: number): Promise<string> {
    const response = await this.fetcher(
      `https://places.googleapis.com/v1/${name}/media?maxWidthPx=${width}&skipHttpRedirect=true`,
      { headers: { "X-Goog-Api-Key": this.key }, signal: AbortSignal.timeout(12000) },
    );
    const media = (await readJson(response, "Place photo")) as { photoUri?: string };
    const uri = safeUrl(media.photoUri);
    if (!uri || !new URL(uri).hostname.endsWith(".googleusercontent.com"))
      throw new Error("Photo unavailable");
    return uri;
  }
  async routes(input: RoutePreviewRequest): Promise<RoutePreview> {
    const results = await Promise.allSettled(
      input.stops.slice(0, -1).map(async (from, index) => {
        const to = input.stops[index + 1]!;
        const location = (stop: typeof from) => ({
          location: { latLng: { latitude: stop.latitude, longitude: stop.longitude } },
        });
        const response = await this.fetcher(
          "https://routes.googleapis.com/directions/v2:computeRoutes",
          {
            method: "POST",
            headers: {
              "content-type": "application/json",
              "X-Goog-Api-Key": this.key,
              "X-Goog-FieldMask":
                "routes.distanceMeters,routes.duration,routes.polyline.encodedPolyline",
            },
            body: JSON.stringify({
              origin: location(from),
              destination: location(to),
              travelMode:
                input.transportation === "transit"
                  ? "TRANSIT"
                  : input.transportation === "walking"
                    ? "WALK"
                    : "DRIVE",
              polylineQuality: "HIGH_QUALITY",
              ...(input.transportation === "transit"
                ? {
                    departureTime: from.departureTime,
                    transitPreferences: {
                      routingPreference:
                        input.transitPreference === "fewer_transfers"
                          ? "FEWER_TRANSFERS"
                          : "LESS_WALKING",
                    },
                  }
                : {}),
            }),
            signal: AbortSignal.timeout(12000),
          },
        );
        const body = (await readJson(response, "Route preview")) as {
          routes?: Array<{
            distanceMeters?: number;
            duration?: string;
            polyline?: { encodedPolyline?: string };
          }>;
        };
        const route = body.routes?.[0];
        if (!route) throw new Error("Route unavailable");
        return {
          fromPlaceId: from.placeId,
          toPlaceId: to.placeId,
          distanceMeters: route.distanceMeters ?? 0,
          durationMinutes: Number((route.duration ?? "0s").replace("s", "")) / 60,
          encodedPolyline: route.polyline?.encodedPolyline ?? null,
        };
      }),
    );
    return RoutePreviewSchema.parse({
      legs: results.flatMap((result) => (result.status === "fulfilled" ? [result.value] : [])),
      warnings: results.flatMap((result, index) =>
        result.status === "rejected" || !result.value.encodedPolyline
          ? [`Route between stops ${index + 1} and ${index + 2} is unavailable.`]
          : [],
      ),
    });
  }
}
