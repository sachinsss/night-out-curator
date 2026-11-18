import { randomUUID } from "node:crypto";
import {
  PlanningOutputSchema,
  SearchPlanSchema,
  type PlanningOutput,
  type RecommendationRequest,
  type RecommendationResponse,
  type SearchPlan,
  type Venue,
} from "@night-out/contracts";
import type { DiscoveryAgentLike } from "../agents/discovery-agent.js";
import type { PlanningAgentLike, PlanningInput } from "../agents/planning-agent.js";
import type { CacheKeyParts } from "../cache/sqlite-cache.js";
import { filterVenues } from "../domain/filter-venues.js";
import { rankVenues } from "../domain/rank-venues.js";
import { itineraryFailures } from "../domain/validate-itinerary.js";
import type { PlacesClient } from "../integrations/places/places-client.js";
import type { RoutesClient } from "../integrations/routes/routes-client.js";
import type { WeatherClient, WeatherContext } from "../integrations/weather/weather-client.js";

interface CacheLike {
  createKey(parts: CacheKeyParts): string;
  get<T>(key: string): T | null;
  set(key: string, value: unknown, ttlMs: number): void;
}
interface CacheIdentity {
  provider: string;
  model: string;
}

export interface WorkflowDependencies {
  discoveryAgent: DiscoveryAgentLike;
  planningAgent: PlanningAgentLike;
  places: PlacesClient;
  weather: WeatherClient;
  routes: RoutesClient;
  cache?: CacheLike;
  cacheIdentities?: { discovery: CacheIdentity; planning: CacheIdentity };
}

const PRICE_ESTIMATES: Record<string, number> = {
  PRICE_LEVEL_FREE: 0,
  PRICE_LEVEL_INEXPENSIVE: 15,
  PRICE_LEVEL_MODERATE: 30,
  PRICE_LEVEL_EXPENSIVE: 60,
  PRICE_LEVEL_VERY_EXPENSIVE: 100,
};

export class RecommendationWorkflow {
  constructor(private readonly dependencies: WorkflowDependencies) {}

  async run(request: RecommendationRequest): Promise<RecommendationResponse> {
    const discoveryKey = this.key("discovery", request, "discovery-v1");
    const cachedDiscovery = discoveryKey
      ? this.dependencies.cache?.get<SearchPlan>(discoveryKey)
      : null;
    const [searchPlan, weather] = await Promise.all([
      cachedDiscovery
        ? Promise.resolve(SearchPlanSchema.parse(cachedDiscovery))
        : this.dependencies.discoveryAgent.run(request),
      this.dependencies.weather
        .getHourly({
          latitude: request.location.latitude,
          longitude: request.location.longitude,
          hours: 8,
        })
        .catch(() => null),
    ]);
    if (!cachedDiscovery && discoveryKey)
      this.dependencies.cache?.set(discoveryKey, searchPlan, 30 * 24 * 60 * 60 * 1000);
    const results = await Promise.all(
      searchPlan.queries.map((query) =>
        this.dependencies.places.textSearch({
          query,
          latitude: request.location.latitude,
          longitude: request.location.longitude,
          radiusMeters: searchPlan.radiusMeters,
        }),
      ),
    );
    const venues = rankVenues(filterVenues(results.flat(), request), request).slice(0, 20);
    const venueMap = new Map(venues.map((venue) => [venue.placeId, venue]));
    const cacheState = { discoveryHit: Boolean(cachedDiscovery), planningHit: false };
    if (!venues.length)
      return this.unresolved(weather, ["No matching venues were found."], cacheState);

    const planningInput: PlanningInput = { request, venues, weather };
    const planningKey = this.key(
      "planning",
      {
        request,
        candidatePlaceIds: venues.map((venue) => venue.placeId),
        weather: weather?.summary ?? null,
      },
      "planning-v1",
    );
    const cachedPlanning = planningKey
      ? this.dependencies.cache?.get<PlanningOutput>(planningKey)
      : null;
    let planning = cachedPlanning
      ? PlanningOutputSchema.parse(cachedPlanning)
      : await this.dependencies.planningAgent.run(planningInput);
    cacheState.planningHit = Boolean(cachedPlanning);
    if (!cachedPlanning && planningKey)
      this.dependencies.cache?.set(planningKey, planning, 24 * 60 * 60 * 1000);
    let failures = itineraryFailures(planning, venueMap, request);
    if (failures.length) {
      planning = await this.dependencies.planningAgent.run({
        ...planningInput,
        failedChecks: failures,
      });
      failures = itineraryFailures(planning, venueMap, request);
      if (!failures.length && planningKey)
        this.dependencies.cache?.set(planningKey, planning, 24 * 60 * 60 * 1000);
    }
    if (failures.length) return this.unresolved(weather, failures, cacheState);
    return this.buildResponse(request, planning, venueMap, weather, cacheState);
  }

  private key(
    agent: "discovery" | "planning",
    input: unknown,
    promptVersion: string,
  ): string | null {
    const identity = this.dependencies.cacheIdentities?.[agent];
    if (!this.dependencies.cache || !identity) return null;
    return this.dependencies.cache.createKey({
      agent,
      provider: identity.provider,
      model: identity.model,
      promptVersion,
      schemaVersion: "1",
      input,
    });
  }

  private async buildResponse(
    request: RecommendationRequest,
    planning: PlanningOutput,
    venueMap: Map<string, Venue>,
    weather: WeatherContext | null,
    cache: { discoveryHit: boolean; planningHit: boolean },
  ): Promise<RecommendationResponse> {
    const itineraries = await Promise.all(
      planning.itineraries.map(async (itinerary) => {
        const selected = itinerary.stops.map((stop) => venueMap.get(stop.placeId)!);
        const routeOptions = {
          departureTimes: itinerary.stops.map(
            (stop) => `${request.date}T${stop.startTime}:00-07:00`,
          ),
          ...(request.transitPreference ? { transitPreference: request.transitPreference } : {}),
        };
        const routeLegs = await this.dependencies.routes
          .compute(
            selected.map((venue) => ({
              placeId: venue.placeId,
              latitude: venue.location.latitude,
              longitude: venue.location.longitude,
            })),
            request.transportation,
            routeOptions,
          )
          .catch(() => []);
        const transitWarnings = routeLegs
          .flatMap((leg) => leg.realtime?.alerts ?? [])
          .concat(
            routeLegs.flatMap((leg) =>
              leg.realtime?.delayMinutes
                ? [`Valley Metro reports a ${leg.realtime.delayMinutes}-minute delay.`]
                : [],
            ),
          );
        const routeWarnings =
          selected.length > 1 && routeLegs.length !== selected.length - 1
            ? ["Travel routes could not be verified for every stop."]
            : [];
        const warnings = [
          ...new Set([
            ...selected.flatMap((venue) => venue.warnings),
            ...transitWarnings,
            ...routeWarnings,
          ]),
        ];
        const estimated = selected.every((venue) => venue.priceLevel)
          ? selected.reduce((total, venue) => total + (PRICE_ESTIMATES[venue.priceLevel!] ?? 0), 0)
          : null;
        return {
          id: randomUUID(),
          title: itinerary.title,
          summary: itinerary.summary,
          stops: itinerary.stops.map((stop, index) => ({
            venue: selected[index]!,
            startTime: stop.startTime,
            durationMinutes: stop.durationMinutes,
            reason: stop.reason,
          })),
          routeLegs,
          estimatedCostPerPerson: estimated,
          warnings,
        };
      }),
    );
    const warnings = [
      ...new Set([...itineraries.flatMap((item) => item.warnings), ...(weather?.warnings ?? [])]),
    ];
    const status =
      warnings.length || itineraries.some((item) => item.estimatedCostPerPerson == null)
        ? "provisional"
        : "valid";
    return {
      requestId: randomUUID(),
      status,
      itineraries,
      weather: weather ? { summary: weather.summary, warnings: weather.warnings } : null,
      warnings,
      generatedAt: new Date().toISOString(),
      cache,
    };
  }

  private unresolved(
    weather: WeatherContext | null,
    warnings: string[],
    cache: { discoveryHit: boolean; planningHit: boolean },
  ): RecommendationResponse {
    return {
      requestId: randomUUID(),
      status: "unresolved",
      itineraries: [],
      weather: weather ? { summary: weather.summary, warnings: weather.warnings } : null,
      warnings,
      generatedAt: new Date().toISOString(),
      cache,
    };
  }
}
