import { ArrowUpRight, ChevronRight } from "lucide-react";
import type { RecommendationRequest } from "@night-out/contracts";
import { Popover, PopoverContent, PopoverTrigger } from "./components/ui/popover";
import { mapsLink, type ItineraryStop } from "./result-utils";
export function MapsAction({
  stops,
  request,
  compact = false,
}: {
  stops: ItineraryStop[];
  request: RecommendationRequest;
  compact?: boolean;
}) {
  const className = compact ? "open-maps-outline" : "open-maps-button";
  if (request.transportation !== "transit" || stops.length < 3)
    return (
      <a className={className} href={mapsLink(stops, request)} target="_blank" rel="noreferrer">
        Open in Maps
        <ArrowUpRight />
      </a>
    );
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button type="button" className={className}>
          Open in Maps
          <ArrowUpRight />
        </button>
      </PopoverTrigger>
      <PopoverContent className="maps-leg-popover" align="end">
        <h3>Choose a transit leg</h3>
        <p>Google Maps opens transit directions one leg at a time.</p>
        <ol>
          {stops.slice(0, -1).map((stop, index) => (
            <li key={stop.venue.placeId}>
              <a
                href={mapsLink([stop, stops[index + 1]!], request)}
                target="_blank"
                rel="noreferrer"
              >
                <span>
                  {index + 1}
                  <ChevronRight />
                  {index + 2}
                </span>
                <strong>
                  {stop.venue.name}
                  <small>to {stops[index + 1]!.venue.name}</small>
                </strong>
                <ArrowUpRight />
              </a>
            </li>
          ))}
        </ol>
      </PopoverContent>
    </Popover>
  );
}
