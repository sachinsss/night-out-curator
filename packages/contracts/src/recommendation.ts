import { z } from "zod";

export const LocationSchema = z.object({
  latitude: z.number().min(-90).max(90),
  longitude: z.number().min(-180).max(180),
  label: z.string().trim().min(1).max(120),
});

export const RecommendationRequestSchema = z.object({
  location: LocationSchema,
  date: z.string().regex(/^\d{4}-\d{2}-\d{2}$/),
  startTime: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  partySize: z.number().int().min(1).max(20),
  budgetPerPerson: z.number().positive().max(10_000),
  currency: z.literal("USD"),
  preferences: z.array(z.string().trim().min(1).max(80)).min(1).max(12),
  excludedCategories: z.array(z.string().trim().min(1).max(80)).max(12).default([]),
  transportation: z.enum(["walking", "driving", "rideshare", "transit"]),
  transitPreference: z.enum(["less_walking", "fewer_transfers"]).optional(),
  stopCount: z.number().int().min(1).max(4),
});

export const SearchPlanSchema = z.object({
  queries: z.array(z.string().trim().min(1).max(120)).min(1).max(5),
  includedTypes: z.array(z.string().trim().min(1).max(80)).max(10),
  excludedTypes: z.array(z.string().trim().min(1).max(80)).max(10),
  radiusMeters: z.number().int().min(100).max(50_000),
  priorities: z.array(z.string().trim().min(1).max(100)).max(8),
});

export const VenueSchema = z.object({
  placeId: z.string().min(1),
  name: z.string().min(1),
  category: z.string().min(1),
  address: z.string().default(""),
  location: LocationSchema.omit({ label: true }),
  businessStatus: z.string().nullable().default(null),
  priceLevel: z.string().nullable().default(null),
  rating: z.number().min(0).max(5).nullable().default(null),
  userRatingCount: z.number().int().nonnegative().nullable().default(null),
  regularOpeningHours: z.unknown().nullable().default(null),
  mapsUri: z.string().url().nullable().default(null),
  retrievedAt: z.string().datetime(),
  distanceMeters: z.number().nonnegative().nullable().default(null),
  relevanceScore: z.number().min(0).max(1).default(0),
  warnings: z.array(z.string()).default([]),
});

export const PlanningStopSchema = z.object({
  placeId: z.string().min(1),
  startTime: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
  durationMinutes: z.number().int().min(15).max(300),
  reason: z.string().trim().min(1).max(300),
});

export const PlanningOutputSchema = z.object({
  itineraries: z
    .array(
      z.object({
        title: z.string().trim().min(1).max(100),
        summary: z.string().trim().min(1).max(500),
        stops: z.array(PlanningStopSchema).min(1).max(4),
      }),
    )
    .min(1)
    .max(3),
});

export const TransitSegmentSchema = z.object({
  routeId: z.string().nullable().default(null),
  lineName: z.string(),
  headsign: z.string().nullable().default(null),
  departureStop: z.string(),
  arrivalStop: z.string(),
  departureTime: z.string().nullable().default(null),
  arrivalTime: z.string().nullable().default(null),
  stopCount: z.number().int().nonnegative().nullable().default(null),
  vehicleType: z.string().nullable().default(null),
});

export const TransitRealtimeSchema = z.object({
  status: z.enum(["on_time", "delayed", "alert", "unavailable"]),
  delayMinutes: z.number().nullable(),
  alerts: z.array(z.string()),
  checkedAt: z.string().datetime(),
});

export const RouteLegSchema = z.object({
  fromPlaceId: z.string(),
  toPlaceId: z.string(),
  distanceMeters: z.number().nonnegative(),
  durationMinutes: z.number().nonnegative(),
  mode: z.enum(["walking", "driving", "transit"]),
  transitSegments: z.array(TransitSegmentSchema).default([]),
  realtime: TransitRealtimeSchema.nullable().default(null),
});

export const RecommendationStatusSchema = z.enum(["valid", "provisional", "unresolved"]);

export const RecommendationResponseSchema = z.object({
  requestId: z.string().uuid(),
  status: RecommendationStatusSchema,
  itineraries: z.array(
    z.object({
      id: z.string().uuid(),
      title: z.string(),
      summary: z.string(),
      stops: z.array(
        z.object({
          venue: VenueSchema,
          startTime: z.string(),
          durationMinutes: z.number(),
          reason: z.string(),
        }),
      ),
      routeLegs: z.array(RouteLegSchema),
      estimatedCostPerPerson: z.number().nonnegative().nullable(),
      warnings: z.array(z.string()),
    }),
  ),
  weather: z.object({ summary: z.string(), warnings: z.array(z.string()) }).nullable(),
  warnings: z.array(z.string()),
  generatedAt: z.string().datetime(),
  cache: z.object({ discoveryHit: z.boolean(), planningHit: z.boolean() }),
});

export function validatePlanningCandidates(
  output: PlanningOutput,
  candidateIds: ReadonlySet<string>,
): PlanningOutput {
  for (const itinerary of output.itineraries) {
    for (const stop of itinerary.stops) {
      if (!candidateIds.has(stop.placeId)) {
        throw new Error(`Planning output contains unknown Place ID: ${stop.placeId}`);
      }
    }
  }
  return output;
}

export type RecommendationRequest = z.infer<typeof RecommendationRequestSchema>;
export type SearchPlan = z.infer<typeof SearchPlanSchema>;
export type Venue = z.infer<typeof VenueSchema>;
export type PlanningOutput = z.infer<typeof PlanningOutputSchema>;
export type RecommendationResponse = z.infer<typeof RecommendationResponseSchema>;
export type RouteLeg = z.infer<typeof RouteLegSchema>;
