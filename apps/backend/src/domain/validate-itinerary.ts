import type { PlanningOutput, RecommendationRequest, Venue } from "@night-out/contracts";

export function itineraryFailures(
  output: PlanningOutput,
  candidates: ReadonlyMap<string, Venue>,
  request: RecommendationRequest,
): string[] {
  const failures: string[] = [];
  for (const itinerary of output.itineraries) {
    if (itinerary.stops.length !== request.stopCount)
      failures.push(`Itinerary must contain ${request.stopCount} stops.`);
    for (const stop of itinerary.stops)
      if (!candidates.has(stop.placeId)) failures.push(`Unknown Place ID: ${stop.placeId}`);
  }
  return [...new Set(failures)];
}
