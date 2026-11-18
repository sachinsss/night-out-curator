import { useEffect, useState, type FormEvent } from "react";
import type { MapPoint } from "./map-point";
import type { RecommendationRequest, RecommendationResponse } from "@night-out/contracts";
import { createRecommendation, resolveLocation, type ResolvedLocation } from "./api";
import { BrandMark } from "./BrandMark";
import { ItineraryDashboard } from "./ItineraryDashboard";
import { PlannerForm, type Transportation } from "./PlannerForm";

const dinnerLayer = new URL("../public/images/phoenix-dinner-night-layer.png", import.meta.url)
  .href;

const PHOENIX = { lat: 33.4484, lng: -112.074 };

export function App() {
  const [view, setView] = useState<"planner" | "results">("planner");
  const [result, setResult] = useState<RecommendationResponse | null>(null);
  const [request, setRequest] = useState<RecommendationRequest | null>(null);
  const [location, setLocation] = useState<ResolvedLocation | null>(null);
  const [mapPoint, setMapPoint] = useState<MapPoint>(PHOENIX);
  const [showMap, setShowMap] = useState(false);
  const [transportation, setTransportation] = useState<Transportation>("rideshare");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "Night-Out Curator | Plan your night";
  }, []);

  function currentLocation() {
    setError("");
    if (!navigator.geolocation)
      return setError(
        "Location is not supported by this browser. Enter an address or choose on the map.",
      );
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        const next = {
          label: "Current location",
          latitude: coords.latitude,
          longitude: coords.longitude,
        };
        setLocation(next);
        setMapPoint({ lat: coords.latitude, lng: coords.longitude });
      },
      () => setError("Location permission was denied. Enter an address or choose on the map."),
    );
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    const locationQuery = String(data.get("locationQuery") ?? "").trim();
    const date = String(data.get("date") ?? "");
    const startTime = String(data.get("startTime") ?? "");
    const preferences = ["cuisine", "mood", "dietary", "preferences"]
      .flatMap((name) => String(data.get(name) ?? "").split(","))
      .map((value) => value.trim())
      .filter(Boolean);
    if (!location && !locationQuery)
      return setError("Enter an address or choose a location on the map.");
    if (!date) return setError("Choose a date for your night out.");
    if (!startTime) return setError("Choose a start time.");
    if (!preferences.length) return setError("Add at least one preference for your night.");
    setLoading(true);
    setError("");
    try {
      const chosen = location ?? (await resolveLocation(locationQuery));
      const nextRequest: RecommendationRequest = {
        location: chosen,
        date,
        startTime,
        partySize: Number(data.get("partySize")),
        budgetPerPerson: Number(data.get("budget")),
        currency: "USD",
        preferences,
        excludedCategories: String(data.get("excluded") ?? "")
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean),
        transportation,
        stopCount: Number(data.get("stopCount")),
        ...(transportation === "transit"
          ? {
              transitPreference: String(data.get("transitPreference")) as
                "less_walking" | "fewer_transfers",
            }
          : {}),
      };
      setLocation(chosen);
      const nextResult = await createRecommendation(nextRequest);
      setRequest(nextRequest);
      setResult(nextResult);
      setView("results");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  function editPlan() {
    setView("planner");
    setError("");
  }
  const showingResults = view === "results" && Boolean(result && request);
  const city = request?.location.label.split(",")[0] || "Phoenix";
  return (
    <div className={`app-shell${showingResults ? " app-shell-results" : ""}`}>
      <header className="topbar">
        <a className="brand" href="#main">
          <BrandMark surface="dark" />
          Night-Out Curator
        </a>
      </header>
      <main id="main" className="page-grid">
        <section className="hero-panel" aria-labelledby="page-title">
          <h1 id="page-title">
            Plan the
            <br />
            Perfect Night
            <br />
            in <em>{city}</em>
          </h1>
          <p>
            {result?.itineraries[0]?.summary ??
              "Food, drinks, and city experiences curated around your vibe, budget, and time."}
          </p>
          <svg className="hero-swoosh" viewBox="0 0 300 34" aria-hidden="true">
            <path
              d="M2 27 Q100 -10 205 18 T299 22"
              fill="none"
              stroke="currentColor"
              strokeWidth="6"
            />
          </svg>
          <div className="scene-foreground">
            <img
              src={dinnerLayer}
              width={1536}
              height={1024}
              alt="Fresh pasta and a cocktail on a moonlit desert stone ledge"
            />
          </div>
        </section>
        <section
          className="dashboard"
          aria-label={showingResults ? "Generated itinerary" : "Night planner"}
        >
          <div className="dashboard-accent" />
          {result && request && (
            <div className="result-screen" hidden={!showingResults}>
              <ItineraryDashboard
                key={result.requestId}
                result={result}
                request={request}
                onReset={editPlan}
                active={showingResults}
              />
            </div>
          )}
          <div className="planner-screen" hidden={showingResults}>
            <PlannerForm
              onReturnToResults={result && request ? () => setView("results") : undefined}
              loading={loading}
              error={error}
              location={location}
              mapPoint={mapPoint}
              showMap={showMap}
              transportation={transportation}
              onSubmit={submit}
              onUseLocation={currentLocation}
              onToggleMap={() => setShowMap((value) => !value)}
              onMapChange={(point) => {
                setMapPoint(point);
                setLocation({
                  label: "Selected map location",
                  latitude: point.lat,
                  longitude: point.lng,
                });
              }}
              onLocationQuery={() => setLocation(null)}
              onTransportation={setTransportation}
            />
          </div>
        </section>
      </main>
    </div>
  );
}
