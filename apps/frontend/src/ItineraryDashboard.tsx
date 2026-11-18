import { useEffect, useRef, useState } from "react";
import type {
  RecommendationRequest,
  RecommendationResponse,
  RoutePreview,
} from "@night-out/contracts";
import {
  AlertTriangle,
  Check,
  ChevronRight,
  Clock3,
  DollarSign,
  Map,
  Route,
  UsersRound,
  Star,
  CarFront,
  RefreshCw,
} from "lucide-react";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "./components/ui/tabs";
import { Button } from "./components/ui/button";
import { MapsAction } from "./MapsAction";
import { ResultMap } from "./ResultMap";
import { VenuePhoto } from "./VenuePhoto";
import { VenueDetails } from "./VenueDetails";
import { useVenuePresentation } from "./use-venue-presentation";
import { fetchRoutePreview } from "./presentation-api";
import { schedule, clock, categoryLabel, priceLabel } from "./result-utils";
import "./results.css";

type View = "itinerary" | "map" | "details";
export function ItineraryDashboard({
  result,
  request,
  onReset,
  active = true,
}: {
  result: RecommendationResponse;
  request: RecommendationRequest;
  onReset(): void;
  active?: boolean;
}) {
  const [tab, setTab] = useState<View>("itinerary");
  const [selected, setSelected] = useState(0);
  const [mapVisited, setMapVisited] = useState(false);
  const [preview, setPreview] = useState<RoutePreview | null>(null);
  const [routeLoading, setRouteLoading] = useState(false);
  const [routeError, setRouteError] = useState("");
  const [routeAttempt, setRouteAttempt] = useState(0);
  const plan = result.itineraries[0];
  const stops = plan?.stops ?? [];
  const { states, retry } = useVenuePresentation(stops.map((stop) => stop.venue.placeId));
  const timings = schedule(stops, request.date);
  const pendingRoute = useRef<Promise<RoutePreview> | null>(null);
  useEffect(() => {
    if (!mapVisited || !plan || !active) return;
    let current = true;
    setRouteLoading(true);
    setRouteError("");
    if (!pendingRoute.current)
      pendingRoute.current = fetchRoutePreview({
        stops: stops.map((stop, i) => ({
          placeId: stop.venue.placeId,
          ...stop.venue.location,
          departureTime: timings[i]!.departureTime,
        })),
        transportation: request.transportation,
        ...(request.transitPreference ? { transitPreference: request.transitPreference } : {}),
      });
    pendingRoute.current
      .then((value) => {
        if (current) {
          setPreview(value);
          setRouteLoading(false);
        }
      })
      .catch(() => {
        if (current) {
          setRouteError("Your route could not load. Stop locations are still available.");
          setRouteLoading(false);
        }
      });
    return () => {
      current = false;
    };
  }, [mapVisited, routeAttempt, active]);
  if (!plan || !stops.length)
    return (
      <section className="results-empty">
        <AlertTriangle />
        <h2>No feasible route yet</h2>
        <p>{result.warnings[0] ?? "Try a wider budget, fewer stops, or another area."}</p>
        <Button type="button" onClick={onReset}>
          Adjust plan
        </Button>
      </section>
    );
  const routeIncomplete = stops.length > 1 && plan.routeLegs.length !== stops.length - 1;
  const status =
    result.status === "valid" && (routeIncomplete || routeError || preview?.warnings.length)
      ? "provisional"
      : result.status;
  const legs = preview?.legs.length === stops.length - 1 ? preview.legs : plan.routeLegs;
  const available = stops.length === 1 || legs.length === stops.length - 1;
  const minutes = available
    ? Math.round(legs.reduce((sum, leg) => sum + leg.durationMinutes, 0))
    : null;
  const miles = available
    ? legs.reduce((sum, leg) => sum + leg.distanceMeters, 0) / 1609.344
    : null;
  const duration = (timings.at(-1)!.end - timings[0]!.start) / 60;
  const travel = {
    rideshare: "Rideshare",
    driving: "Driving",
    walking: "Walking",
    transit: "Public transit",
  }[request.transportation];
  const warnings = [
    ...new Set([
      ...result.warnings,
      ...plan.warnings,
      ...(routeIncomplete ? ["Some travel routes have not been verified."] : []),
      ...(preview?.warnings ?? []),
    ]),
  ];
  function selectStop(index: number) {
    setSelected(index);
    setTab("details");
  }
  const titles = {
    itinerary: ["Your Night Out Route", plan.summary],
    map: ["Your Route on Map", "See your stops, travel times, and the route between them."],
    details: ["Trip Details", "Everything you need for a smooth night out."],
  };
  return (
    <section className="results-shell">
      <Tabs
        value={tab}
        onValueChange={(value) => {
          setTab(value as View);
          if (value === "map") setMapVisited(true);
        }}
        className="results-tabs"
      >
        <header className="results-toolbar">
          <TabsList aria-label="Itinerary views" className="results-tab-list">
            <TabsTrigger value="itinerary">Itinerary</TabsTrigger>
            <TabsTrigger value="map">Map</TabsTrigger>
            <TabsTrigger value="details">Details</TabsTrigger>
          </TabsList>
          <span className={`verification-badge ${status}`}>
            {status === "valid" ? <Check /> : <AlertTriangle />}
            {status === "valid"
              ? "Verified"
              : status === "provisional"
                ? "Provisional"
                : "Unresolved"}
          </span>
        </header>
        <div className="results-heading">
          <div>
            <h2>{titles[tab][0]}</h2>
            <p>{titles[tab][1]}</p>
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={onReset} className="edit-plan">
            Edit plan
          </Button>
        </div>
        <TabsContent value="itinerary" className="result-tab-panel">
          <div className="itinerary-layout">
            <div className="stop-timeline">
              {stops.map((stop, index) => {
                const state = states[stop.venue.placeId];
                const price = priceLabel(stop.venue.priceLevel);
                return (
                  <article className="timeline-item" key={stop.venue.placeId}>
                    <span className="timeline-number">{index + 1}</span>
                    <div className="stop-card">
                      <VenuePhoto
                        name={stop.venue.name}
                        photos={state?.data?.photos}
                        loading={state?.loading ?? true}
                      />
                      <button
                        type="button"
                        className="stop-card-action"
                        onClick={() => selectStop(index)}
                        aria-label={`View details for ${stop.venue.name}`}
                      >
                        <span className="stop-card-copy">
                          <strong>{stop.venue.name}</strong>
                          <span className="stop-category">
                            {state?.data?.displayCategory ?? categoryLabel(stop.venue.category)}
                            {price && ` · ${price}`}
                          </span>
                          <span className="stop-card-meta">
                            <span className="stop-rating">
                              <Star />
                              {stop.venue.rating?.toFixed(1) ?? "Not rated"}
                              {stop.venue.userRatingCount != null && (
                                <small>
                                  (
                                  {Intl.NumberFormat("en-US", {
                                    notation: "compact",
                                    maximumFractionDigits: 1,
                                  }).format(stop.venue.userRatingCount)}
                                  )
                                </small>
                              )}
                            </span>
                            <span className="stop-time">{timings[index]!.label}</span>
                          </span>
                        </span>
                        <ChevronRight />
                      </button>
                    </div>
                    {state?.error && (
                      <div className="thumbnail-error">
                        <span>Photo details unavailable</span>
                        <button type="button" onClick={() => retry(stop.venue.placeId)}>
                          Retry
                        </button>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
            <aside className="glance-card">
              <h3>Itinerary at a Glance</h3>
              <dl>
                <div>
                  <Map />
                  <dt>Stops</dt>
                  <dd>
                    {stops.length} {stops.length === 1 ? "stop" : "stops"}
                  </dd>
                </div>
                <div>
                  <Clock3 />
                  <dt>Duration</dt>
                  <dd>
                    ~ {Number(duration.toFixed(1))} hr{" "}
                    <small>
                      ({clock(timings[0]!.start)} - {clock(timings.at(-1)!.end)})
                    </small>
                  </dd>
                </div>
                <div>
                  <CarFront />
                  <dt>Transportation</dt>
                  <dd>{travel}</dd>
                </div>
                <div>
                  <DollarSign />
                  <dt>Cost</dt>
                  <dd>
                    {plan.estimatedCostPerPerson == null
                      ? "Cost unavailable"
                      : `$${Math.round(plan.estimatedCostPerPerson)} est. per person`}
                  </dd>
                </div>
                <div>
                  <UsersRound />
                  <dt>Party size</dt>
                  <dd>
                    {request.partySize} {request.partySize === 1 ? "person" : "people"}
                  </dd>
                </div>
              </dl>
              <MapsAction stops={stops} request={request} />
            </aside>
          </div>
          <p className="google-data-credit">Venue information and photos from Google Maps.</p>
        </TabsContent>
        <TabsContent
          value="map"
          forceMount={mapVisited || undefined}
          className="result-tab-panel map-tab-panel"
        >
          {mapVisited && (
            <>
              <ResultMap
                itinerary={plan}
                preview={preview}
                onSelect={selectStop}
                selectedIndex={selected}
                active={active && tab === "map"}
              />
              {routeLoading && (
                <p className="route-feedback" role="status">
                  <span className="result-spinner" />
                  Finding your route...
                </p>
              )}
              {(routeError || Boolean(preview?.warnings.length)) && (
                <div className="route-feedback route-warning" role="status">
                  <span>{routeError || preview?.warnings.join(" ")}</span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      pendingRoute.current = null;
                      setRouteAttempt((value) => value + 1);
                    }}
                  >
                    <RefreshCw data-icon="inline-start" />
                    Retry route
                  </Button>
                </div>
              )}
              <div className="map-summary">
                <div>
                  <Route />
                  <span>
                    <small>Total distance</small>
                    <strong>
                      {miles == null ? "Unavailable" : `${Number(miles.toFixed(1))} mi`}
                    </strong>
                  </span>
                </div>
                <div>
                  <Clock3 />
                  <span>
                    <small>Travel time</small>
                    <strong>{minutes == null ? "Unavailable" : `~ ${minutes} min`}</strong>
                  </span>
                </div>
                <div>
                  <CarFront />
                  <span>
                    <small>Transportation</small>
                    <strong>{travel}</strong>
                  </span>
                </div>
                <MapsAction stops={stops} request={request} compact />
              </div>
            </>
          )}
        </TabsContent>
        <TabsContent value="details" className="result-tab-panel details-tab-panel">
          <VenueDetails
            stops={stops}
            index={selected}
            onSelect={setSelected}
            state={states[stops[selected]!.venue.placeId]}
            onRetry={() => retry(stops[selected]!.venue.placeId)}
            timeLabel={timings[selected]!.label}
            request={request}
          />
        </TabsContent>
      </Tabs>
      {warnings.length > 0 && (
        <details className="result-warnings">
          <summary>
            {warnings.length} planning {warnings.length === 1 ? "note" : "notes"}
          </summary>
          <ul>
            {warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
