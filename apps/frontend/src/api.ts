import { RecommendationResponseSchema, type RecommendationRequest } from "@night-out/contracts";
export interface ResolvedLocation {
  label: string;
  latitude: number;
  longitude: number;
}
async function message(response: Response, fallback: string) {
  try {
    const body = (await response.json()) as { message?: string };
    return body.message || fallback;
  } catch {
    return fallback;
  }
}
export async function resolveLocation(query: string): Promise<ResolvedLocation> {
  const response = await fetch("/api/v1/locations/resolve", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ query }),
  });
  if (!response.ok) throw new Error(await message(response, "That location could not be found."));
  const value = (await response.json()) as ResolvedLocation;
  if (!value.label || !Number.isFinite(value.latitude) || !Number.isFinite(value.longitude))
    throw new Error("The location service returned an invalid result.");
  return value;
}
export async function createRecommendation(input: RecommendationRequest) {
  const response = await fetch("/api/v1/recommendations", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok)
    throw new Error(
      await message(
        response,
        response.status === 400
          ? "Check the form values and try again."
          : "The curator could not build a plan right now.",
      ),
    );
  return RecommendationResponseSchema.parse(await response.json());
}
