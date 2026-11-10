import type { RecommendationRequest, Venue } from "@night-out/contracts";

export function filterVenues(venues: Venue[], request: RecommendationRequest): Venue[] {
  const excluded = new Set(request.excludedCategories.map((value) => value.toLowerCase()));
  return [
    ...new Map(
      venues
        .filter(
          (venue) =>
            venue.businessStatus !== "CLOSED_PERMANENTLY" &&
            !excluded.has(venue.category.toLowerCase()),
        )
        .map((venue) => [venue.placeId, venue]),
    ).values(),
  ];
}
