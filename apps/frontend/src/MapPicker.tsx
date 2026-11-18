import { useEffect, useRef, useState } from "react";
import type { MapPoint } from "./map-point";
import { loadGoogleMaps, onGoogleMapsAuthFailure } from "./google-maps-loader";
import "./map.css";
import { MapPin } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
  DialogClose,
} from "./components/ui/dialog";
import { Button } from "./components/ui/button";

export function MapPicker({
  value,
  onChange,
  onClose,
}: {
  value: MapPoint;
  onChange(value: MapPoint): void;
  onClose?(): void;
}) {
  const hostRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const onChangeRef = useRef(onChange);
  const valueRef = useRef(value);
  const [state, setState] = useState<"loading" | "ready" | "error">("loading");
  const [error, setError] = useState("");

  onChangeRef.current = onChange;
  valueRef.current = value;

  useEffect(() => {
    let active = true;
    const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY ?? "";
    const mapId = import.meta.env.VITE_GOOGLE_MAPS_MAP_ID?.trim();
    const unsubscribeAuthFailure = onGoogleMapsAuthFailure((cause) => {
      if (!active) return;
      setError(cause.message);
      setState("error");
    });

    loadGoogleMaps(apiKey)
      .then((api) => {
        if (!active || !hostRef.current) return;
        const initialPosition = valueRef.current;
        const map = new api.maps.Map(hostRef.current, {
          center: initialPosition,
          zoom: 13,
          streetViewControl: false,
          mapTypeControl: false,
          fullscreenControl: false,
          clickableIcons: false,
          ...(mapId
            ? { mapId }
            : {
                styles: [
                  { elementType: "geometry", stylers: [{ color: "#14181e" }] },
                  { elementType: "labels.text.fill", stylers: [{ color: "#9da5af" }] },
                  { elementType: "labels.text.stroke", stylers: [{ color: "#14181e" }] },
                  { featureType: "road", elementType: "geometry", stylers: [{ color: "#2b3139" }] },
                  {
                    featureType: "water",
                    elementType: "geometry",
                    stylers: [{ color: "#0d1116" }],
                  },
                ],
              }),
        });
        mapRef.current = map;
        map.panTo(initialPosition);
        setState("ready");
      })
      .catch((cause: unknown) => {
        if (!active) return;
        setError(cause instanceof Error ? cause.message : "Google Maps could not be loaded.");
        setState("error");
      });

    return () => {
      active = false;
      unsubscribeAuthFailure();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const next = { lat: value.lat, lng: value.lng };
    mapRef.current?.panTo(next);
  }, [value.lat, value.lng]);

  return (
    <Dialog
      open
      onOpenChange={(open) => {
        if (!open) onClose?.();
      }}
    >
      <DialogContent
        className="map-picker-dialog"
        showCloseButton={false}
        onCloseAutoFocus={(event) => {
          event.preventDefault();
          document.querySelector<HTMLButtonElement>('button[aria-label="Choose on map"]')?.focus();
        }}
      >
        <DialogHeader className="map-dialog-heading">
          <div className="map-dialog-title-row">
            <div className="map-dialog-icon">
              <MapPin aria-hidden="true" />
            </div>
            <div>
              <DialogTitle>Choose your starting point</DialogTitle>
              <DialogDescription>
                Move the map to place the pin over your location.
              </DialogDescription>
            </div>
          </div>
          <DialogClose asChild>
            <Button type="button" variant="outline" size="sm">
              Cancel
            </Button>
          </DialogClose>
        </DialogHeader>
        <div className="google-map-shell" aria-busy={state === "loading"}>
          <div
            ref={hostRef}
            className="google-map-host"
            aria-label="Choose a location on Google Maps"
          />
          {state === "ready" ? (
            <div className="map-center-pin" aria-hidden="true">
              <MapPin size={42} fill="#ef5b53" stroke="#fff" strokeWidth={1.6} />
            </div>
          ) : null}
          {state === "loading" ? <div className="map-state">Loading Google Maps�</div> : null}
          {state === "error" ? (
            <div className="map-state map-error" role="alert">
              {error}
            </div>
          ) : null}
        </div>
        <DialogFooter className="map-dialog-footer">
          <p>Drag to move. Scroll or pinch to zoom.</p>
          <Button
            type="button"
            disabled={state !== "ready"}
            onClick={() => {
              const center = mapRef.current?.getCenter();
              if (center) {
                onChangeRef.current({ lat: center.lat(), lng: center.lng() });
                onClose?.();
              }
            }}
          >
            Use this location
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
