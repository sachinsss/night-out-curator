import {
  ExternalLink,
  MapPin,
  Clock3,
  Star,
  CarFront,
  CalendarDays,
  UsersRound,
  Utensils,
  RefreshCw,
} from "lucide-react";
import type { RecommendationRequest } from "@night-out/contracts";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./components/ui/tabs";
import { Button } from "./components/ui/button";
import { PlannerSelect } from "./components/planner-controls";
import { VenuePhoto } from "./VenuePhoto";
import { categoryLabel, priceLabel, type ItineraryStop } from "./result-utils";
import type { VenuePresentationState } from "./use-venue-presentation";

export function VenueDetails({
  stops,
  index,
  onSelect,
  state,
  onRetry,
  timeLabel,
  request,
}: {
  stops: ItineraryStop[];
  index: number;
  onSelect(index: number): void;
  state: VenuePresentationState | undefined;
  onRetry(): void;
  timeLabel: string;
  request: RecommendationRequest;
}) {
  const stop = stops[index]!;
  const venue = stop.venue;
  const data = state?.data;
  const maps =
    data?.mapsUri ||
    venue.mapsUri ||
    `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(venue.name)}&query_place_id=${encodeURIComponent(venue.placeId)}`;
  const price = priceLabel(venue.priceLevel);
  return (
    <div className="details-layout">
      <div className="details-main">
        <div className="venue-picker">
          <span>Explore your stops</span>
          <PlannerSelect
            label="Selected venue"
            value={String(index)}
            onValueChange={(value) => onSelect(Number(value))}
            options={stops.map((item, i) => ({
              value: String(i),
              label: `${i + 1}. ${item.venue.name}`,
            }))}
          />
        </div>
        <article className="venue-profile">
          <VenuePhoto
            key={venue.placeId}
            photos={data?.photos}
            name={venue.name}
            loading={state?.loading ?? true}
            gallery
          />
          <div className="venue-profile-info">
            <div className="venue-name-row">
              <h3>{venue.name}</h3>
              <a
                href={maps}
                target="_blank"
                rel="noreferrer"
                aria-label={`Open ${venue.name} in Google Maps`}
              >
                <ExternalLink />
              </a>
            </div>
            <p className="venue-meta">
              <Star />
              {venue.rating?.toFixed(1) ?? "Not rated"}
              {venue.userRatingCount != null && (
                <span>
                  (
                  {Intl.NumberFormat("en-US", {
                    notation: "compact",
                    maximumFractionDigits: 1,
                  }).format(venue.userRatingCount)}
                  )
                </span>
              )}
              <span>{data?.displayCategory ?? categoryLabel(venue.category)}</span>
              {price && <span>{price}</span>}
            </p>
            <p className="venue-address">
              <MapPin />
              {venue.address || "Address unavailable"}
            </p>
            <p className="venue-hours">
              <Clock3 />
              {timeLabel} <span>({stop.durationMinutes} min)</span>
            </p>
          </div>
        </article>
        {state?.error && (
          <div className="enrichment-notice" role="status">
            <span>{state.error}</span>
            <Button type="button" variant="ghost" size="sm" onClick={onRetry}>
              <RefreshCw data-icon="inline-start" />
              Retry
            </Button>
          </div>
        )}
        <Tabs defaultValue="overview" className="venue-sections" key={venue.placeId}>
          <TabsList aria-label="Venue information">
            {["overview", "menu", "reviews", "tips"].map((value) => (
              <TabsTrigger key={value} value={value}>
                {value[0]!.toUpperCase() + value.slice(1)}
              </TabsTrigger>
            ))}
          </TabsList>
          <TabsContent value="overview">
            <p>{stop.reason}</p>
            {data?.summary && data.summary !== stop.reason && <p>{data.summary}</p>}
          </TabsContent>
          <TabsContent value="menu">
            <h4>Plan your order</h4>
            <p>
              {data?.menuUri
                ? "Explore the venue's menu before your visit."
                : data?.websiteUri
                  ? "Visit the venue website for its latest menu and dining information."
                  : "A menu link is not available for this venue. Check its Google Maps page for current information."}
            </p>
            <a
              className="detail-link"
              href={data?.menuUri || data?.websiteUri || maps}
              target="_blank"
              rel="noreferrer"
            >
              {data?.menuUri
                ? "View menu"
                : data?.websiteUri
                  ? "Visit venue website"
                  : "View venue on Google Maps"}
              <ExternalLink />
            </a>
          </TabsContent>
          <TabsContent value="reviews">
            <h4>Hear from other guests</h4>
            <p>
              {venue.rating != null
                ? `${venue.rating.toFixed(1)} out of 5${venue.userRatingCount != null ? ` from ${venue.userRatingCount.toLocaleString()} ratings` : ""}. Read recent guest experiences on Google Maps.`
                : "Reviews are available through the venue's Google Maps page."}
            </p>
            <a
              className="detail-link"
              href={data?.reviewsUri || maps}
              target="_blank"
              rel="noreferrer"
            >
              {data?.reviewsUri ? "Read reviews" : "View venue on Google Maps"}
              <ExternalLink />
            </a>
          </TabsContent>
          <TabsContent value="tips">
            <h4>Planning suggestions</h4>
            <ul>
              <li>Allow time to arrive before your scheduled {timeLabel.split(" - ")[0]} start.</li>
              <li>
                Check current opening hours and any booking requirements directly with the venue.
              </li>
              <li>
                {request.transportation === "transit"
                  ? "Check the final return service before heading out."
                  : request.transportation === "driving"
                    ? "Check parking availability before you leave."
                    : request.transportation === "rideshare"
                      ? "Confirm the pickup point and fare in your rideshare app."
                      : "Wear comfortable shoes and check the walking route."}
              </li>
            </ul>
          </TabsContent>
        </Tabs>
        <p className="google-data-credit">Venue information and photos from Google Maps.</p>
      </div>
      <aside className="planning-card">
        <h3>Info &amp; Planning</h3>
        {Boolean(data?.parking.length) && (
          <div>
            <CarFront />
            <p>
              <strong>Parking</strong>
              <span>{data?.parking.join(" · ")}</span>
            </p>
          </div>
        )}
        {data?.reservable != null && (
          <div>
            <Utensils />
            <p>
              <strong>Reservations</strong>
              <span>{data.reservable ? "Reservations supported" : "Reservations not offered"}</span>
            </p>
          </div>
        )}
        <div>
          <CalendarDays />
          <p>
            <strong>Your date</strong>
            <span>
              {new Date(`${request.date}T12:00:00-07:00`).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
                timeZone: "America/Phoenix",
              })}
            </span>
          </p>
        </div>
        <div>
          <UsersRound />
          <p>
            <strong>Your group</strong>
            <span>
              {request.partySize} {request.partySize === 1 ? "person" : "people"}
            </span>
          </p>
        </div>
        {venue.regularOpeningHours != null && (
          <div>
            <Clock3 />
            <p>
              <strong>Opening hours</strong>
              <a href={maps} target="_blank" rel="noreferrer">
                Check current hours
              </a>
            </p>
          </div>
        )}
      </aside>
    </div>
  );
}
