import { z } from "zod";

export const PhotoResourceSchema = z
  .string()
  .max(1500)
  .regex(/^places\/[A-Za-z0-9_-]+\/photos\/[A-Za-z0-9_=-]+$/);
const SafeUrl = z
  .string()
  .url()
  .refine((value) => new URL(value).protocol === "https:");
export const PlacePresentationSchema = z.object({
  placeId: z.string(),
  displayCategory: z.string().nullable(),
  summary: z.string().nullable(),
  websiteUri: SafeUrl.nullable(),
  mapsUri: SafeUrl.nullable(),
  reviewsUri: SafeUrl.nullable(),
  menuUri: SafeUrl.nullable(),
  reservable: z.boolean().nullable(),
  parking: z.array(z.string()),
  photos: z
    .array(
      z.object({
        name: PhotoResourceSchema,
        sourceUri: SafeUrl.nullable(),
        authors: z.array(z.object({ name: z.string(), uri: SafeUrl.nullable() })),
      }),
    )
    .max(3),
});
export const RoutePreviewRequestSchema = z.object({
  stops: z
    .array(
      z.object({
        placeId: z.string().min(1).max(200),
        latitude: z.number().min(-90).max(90),
        longitude: z.number().min(-180).max(180),
        departureTime: z.string().datetime({ offset: true }),
      }),
    )
    .min(1)
    .max(4),
  transportation: z.enum(["walking", "driving", "rideshare", "transit"]),
  transitPreference: z.enum(["less_walking", "fewer_transfers"]).optional(),
});
export const RoutePreviewSchema = z.object({
  legs: z.array(
    z.object({
      fromPlaceId: z.string(),
      toPlaceId: z.string(),
      distanceMeters: z.number().nonnegative(),
      durationMinutes: z.number().nonnegative(),
      encodedPolyline: z.string().min(1).nullable(),
    }),
  ),
  warnings: z.array(z.string()),
});
export type PlacePresentation = z.infer<typeof PlacePresentationSchema>;
export type RoutePreviewRequest = z.infer<typeof RoutePreviewRequestSchema>;
export type RoutePreview = z.infer<typeof RoutePreviewSchema>;
