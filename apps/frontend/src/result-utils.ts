import type { RecommendationRequest, RecommendationResponse } from "@night-out/contracts";
export type Itinerary = RecommendationResponse["itineraries"][number];
export type ItineraryStop = Itinerary["stops"][number];
export function schedule(stops: ItineraryStop[], date: string) {
  let day = 0;
  let previous = -1;
  return stops.map((stop) => {
    const [hour = 0, minute = 0] = stop.startTime.split(":").map(Number);
    let start = day * 1440 + hour * 60 + minute;
    if (start < previous) {
      day++;
      start += 1440;
    }
    previous = start;
    const end = start + stop.durationMinutes;
    const iso = (minutes: number) =>
      new Date(new Date(`${date}T00:00:00-07:00`).getTime() + minutes * 60000).toISOString();
    return { start, end, departureTime: iso(end), label: `${clock(start)} - ${clock(end)}` };
  });
}
export function clock(minutes: number) {
  const value = ((minutes % 1440) + 1440) % 1440;
  const h = Math.floor(value / 60);
  return `${h % 12 || 12}:${String(value % 60).padStart(2, "0")} ${h < 12 ? "AM" : "PM"}`;
}
export function mapsLink(stops: ItineraryStop[], request: RecommendationRequest) {
  if (request.transportation === "transit" && stops.length > 2) stops = stops.slice(0, 2);
  if (!stops.length) return "https://www.google.com/maps";
  const point = (stop: ItineraryStop) =>
    `${stop.venue.location.latitude},${stop.venue.location.longitude}`;
  if (stops.length === 1)
    return (
      stops[0]!.venue.mapsUri ||
      `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(point(stops[0]!))}&query_place_id=${encodeURIComponent(stops[0]!.venue.placeId)}`
    );
  const params = new URLSearchParams({
    api: "1",
    origin: point(stops[0]!),
    origin_place_id: stops[0]!.venue.placeId,
    destination: point(stops.at(-1)!),
    destination_place_id: stops.at(-1)!.venue.placeId,
    travelmode: request.transportation === "rideshare" ? "driving" : request.transportation,
  });
  if (stops.length > 2) {
    params.set("waypoints", stops.slice(1, -1).map(point).join("|"));
    params.set(
      "waypoint_place_ids",
      stops
        .slice(1, -1)
        .map((stop) => stop.venue.placeId)
        .join("|"),
    );
  }
  return `https://www.google.com/maps/dir/?${params}`;
}
export const categoryLabel = (value: string) =>
  value.replaceAll("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
const PRICES: Record<string, string> = {
  PRICE_LEVEL_FREE: "Free",
  PRICE_LEVEL_INEXPENSIVE: "$",
  PRICE_LEVEL_MODERATE: "$$",
  PRICE_LEVEL_EXPENSIVE: "$$$",
  PRICE_LEVEL_VERY_EXPENSIVE: "$$$$",
};
export const priceLabel = (value: string | null) => PRICES[value ?? ""] ?? null;
export function decodePolyline(encoded: string) {
  const points: google.maps.LatLngLiteral[] = [];
  let index = 0,
    lat = 0,
    lng = 0;
  while (index < encoded.length) {
    const read = () => {
      let result = 0,
        shift = 0,
        byte = 0;
      do {
        if (index >= encoded.length || shift > 30) throw new Error("Invalid route geometry");
        byte = encoded.charCodeAt(index++) - 63;
        result |= (byte & 31) << shift;
        shift += 5;
      } while (byte >= 32);
      return result & 1 ? ~(result >> 1) : result >> 1;
    };
    lat += read();
    lng += read();
    points.push({ lat: lat / 1e5, lng: lng / 1e5 });
  }
  return points;
}
