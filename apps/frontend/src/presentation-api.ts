import {
  PlacePresentationSchema,
  RoutePreviewSchema,
  type RoutePreviewRequest,
} from "@night-out/contracts";

export async function fetchPlacePresentation(placeId: string, signal?: AbortSignal) {
  const response = await fetch(`/api/v1/places/${encodeURIComponent(placeId)}/presentation`, {
    ...(signal ? { signal } : {}),
  });
  if (!response.ok) throw new Error("Venue details could not be loaded.");
  return PlacePresentationSchema.parse(await response.json());
}
export async function fetchRoutePreview(input: RoutePreviewRequest, signal?: AbortSignal) {
  const response = await fetch("/api/v1/routes/preview", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(input),
    ...(signal ? { signal } : {}),
  });
  if (!response.ok) throw new Error("The route could not be loaded.");
  return RoutePreviewSchema.parse(await response.json());
}
export const placePhotoUrl = (name: string, width: 640 | 1280 = 640) =>
  `/api/v1/place-photos?name=${encodeURIComponent(name)}&width=${width}`;
