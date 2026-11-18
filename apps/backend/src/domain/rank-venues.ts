import type { RecommendationRequest, Venue } from "@night-out/contracts";

const PRICE_SCORE: Record<string, number> = {
  PRICE_LEVEL_FREE: 1,
  PRICE_LEVEL_INEXPENSIVE: 0.9,
  PRICE_LEVEL_MODERATE: 0.75,
  PRICE_LEVEL_EXPENSIVE: 0.4,
  PRICE_LEVEL_VERY_EXPENSIVE: 0.2,
};

export function rankVenues(venues: Venue[], request: RecommendationRequest): Venue[] {
  const preferences = request.preferences.map((value) => value.toLowerCase());
  return venues
    .map((venue) => {
      const text = `${venue.name} ${venue.category}`.toLowerCase();
      const preference =
        preferences.filter((value) => text.includes(value)).length / preferences.length;
      const rating = (venue.rating ?? 3) / 5;
      const price = venue.priceLevel ? (PRICE_SCORE[venue.priceLevel] ?? 0.5) : 0.4;
      return {
        ...venue,
        relevanceScore: Math.min(1, preference * 0.45 + rating * 0.35 + price * 0.2),
      };
    })
    .sort((a, b) => b.relevanceScore - a.relevanceScore);
}
