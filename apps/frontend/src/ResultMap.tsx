import { useEffect, useRef, useState } from "react";
import { Layers, RefreshCw } from "lucide-react";
import type { RoutePreview } from "@night-out/contracts";
import { loadGoogleMaps, onGoogleMapsAuthFailure } from "./google-maps-loader";
import { decodePolyline, type Itinerary } from "./result-utils";
import { Button } from "./components/ui/button";

const DARK_MAP = [
  { elementType: "geometry", stylers: [{ color: "#171c23" }] },
  { elementType: "labels.text.fill", stylers: [{ color: "#929ca8" }] },
  { elementType: "labels.text.stroke", stylers: [{ color: "#171c23" }] },
  { featureType: "road", elementType: "geometry", stylers: [{ color: "#303946" }] },
  { featureType: "water", elementType: "geometry", stylers: [{ color: "#0b1118" }] },
  { featureType: "poi", stylers: [{ visibility: "off" }] },
];
export function ResultMap({
  itinerary,
  preview,
  onSelect,
  selectedIndex = 0,
  active = true,
}: {
  itinerary: Itinerary;
  preview: RoutePreview | null;
  onSelect(index: number): void;
  selectedIndex?: number;
  active?: boolean;
}) {
  const host = useRef<HTMLDivElement>(null);
  const map = useRef<google.maps.Map | null>(null);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  const [satellite, setSatellite] = useState(false);
  const select = useRef(onSelect);
  select.current = onSelect;
  useEffect(() => {
    let active = true;
    setReady(false);
    setError("");
    setSatellite(false);
    const unsubscribe = onGoogleMapsAuthFailure(() => {
      if (active) {
        setError("Google Maps could not be authenticated.");
        setReady(false);
      }
    });
    loadGoogleMaps(import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? "")
      .then((api) => {
        if (!active || !host.current) return;
        const first = itinerary.stops[0]?.venue.location;
        map.current = new api.maps.Map(host.current, {
          center: { lat: first?.latitude ?? 33.4484, lng: first?.longitude ?? -112.074 },
          zoom: 14,
          styles: DARK_MAP,
          disableDefaultUI: true,
          zoomControl: true,
          clickableIcons: false,
          gestureHandling: "cooperative",
        });
        setReady(true);
      })
      .catch(() => {
        if (active) setError("The map could not load. Check your connection and try again.");
      });
    return () => {
      active = false;
      unsubscribe();
      map.current = null;
    };
  }, [itinerary.id, attempt]);
  useEffect(() => {
    if (!ready || !map.current || !active) return;
    const api = window.google.maps;
    api.event.trigger(map.current, "resize");
    const bounds = new api.LatLngBounds();
    const lines: google.maps.Polyline[] = [];
    const listeners: google.maps.MapsEventListener[] = [];
    const markers = itinerary.stops.map((stop, index) => {
      const position = { lat: stop.venue.location.latitude, lng: stop.venue.location.longitude };
      bounds.extend(position);
      const marker = new api.Marker({
        map: map.current,
        position,
        title: `${index + 1}. ${stop.venue.name}`,
        label: { text: String(index + 1), color: "#ffffff", fontWeight: "700", fontSize: "14px" },
        icon: {
          path: api.SymbolPath.CIRCLE,
          fillColor: "#ff5000",
          fillOpacity: 1,
          strokeColor: index === selectedIndex ? "#ffffff" : "#ff7c3f",
          strokeWeight: index === selectedIndex ? 3 : 1,
          scale: 17,
        },
        zIndex: 10,
      });
      listeners.push(marker.addListener("click", () => select.current(index)));
      return marker;
    });
    for (const leg of preview?.legs ?? []) {
      if (!leg.encodedPolyline) continue;
      try {
        const path = decodePolyline(leg.encodedPolyline);
        path.forEach((p) => bounds.extend(p));
        lines.push(
          new api.Polyline({
            map: map.current,
            path,
            strokeColor: "#ff5000",
            strokeWeight: 5,
            strokeOpacity: 1,
            zIndex: 2,
          }),
        );
      } catch {
        continue;
      }
    }
    if (itinerary.stops.length > 1)
      map.current.fitBounds(bounds, { top: 45, right: 50, bottom: 45, left: 45 });
    return () => {
      listeners.forEach((listener) => listener.remove());
      markers.forEach((marker) => marker.setMap(null));
      lines.forEach((line) => line.setMap(null));
    };
  }, [ready, itinerary, preview, selectedIndex, active]);
  return (
    <div className="result-map google-result-map" aria-label="Itinerary route map">
      <div ref={host} className="result-google-host" />
      {!ready && !error && (
        <div className="result-map-state" role="status">
          <span className="result-spinner" />
          Loading your map
        </div>
      )}
      {error && (
        <div className="result-map-state" role="alert">
          <p>{error}</p>
          <Button type="button" variant="outline" onClick={() => setAttempt((value) => value + 1)}>
            <RefreshCw data-icon="inline-start" />
            Retry map
          </Button>
        </div>
      )}
      {ready && (
        <Button
          type="button"
          variant="outline"
          className="map-layer-toggle"
          aria-label={satellite ? "Show street map" : "Show satellite map"}
          onClick={() => {
            map.current?.setMapTypeId(satellite ? "roadmap" : "satellite");
            setSatellite(!satellite);
          }}
        >
          <Layers data-icon="inline-start" />
          {satellite ? "Street" : "Satellite"}
        </Button>
      )}
    </div>
  );
}
