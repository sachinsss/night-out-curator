import cors from "@fastify/cors";
import swagger from "@fastify/swagger";
import {
  RecommendationRequestSchema,
  RecommendationResponseSchema,
  PhotoResourceSchema,
  RoutePreviewRequestSchema,
  PlacePresentationSchema,
  RoutePreviewSchema,
  type RecommendationResponse,
} from "@night-out/contracts";
import Fastify from "fastify";
import type { Geocoder } from "./integrations/geocoding/geocoder.js";
import {
  MemoryRecommendationRepository,
  type RecommendationRepository,
} from "./repositories/recommendation-repository.js";

import type { ResultPresentationService } from "./presentation/google-result-presentation.js";

export interface WorkflowLike {
  run(
    request: ReturnType<typeof RecommendationRequestSchema.parse>,
  ): Promise<RecommendationResponse>;
}
export interface AppOptions {
  workflow: WorkflowLike;
  repository?: RecommendationRepository;
  geocoder?: Geocoder;
  enableDevRoutes: boolean;
  frontendOrigin?: string;
  presentation?: ResultPresentationService;
}

export function buildApp(options: AppOptions) {
  const app = Fastify({ logger: false, bodyLimit: 1_000_000 });
  const repository = options.repository ?? new MemoryRecommendationRepository();
  void app.register(cors, { origin: options.frontendOrigin ?? false });
  void app.register(swagger, {
    openapi: { info: { title: "Night-Out Curator API", version: "0.1.0" } },
  });
  app.get("/api/v1/health", async () => ({
    status: "ok",
    agents: 2,
    database: "ready",
    timestamp: new Date().toISOString(),
  }));

  app.post("/api/v1/locations/resolve", async (request, reply) => {
    const query =
      typeof (request.body as { query?: unknown } | null)?.query === "string"
        ? (request.body as { query: string }).query.trim()
        : "";
    if (query.length < 3 || query.length > 200)
      return reply.code(400).send({ error: "INVALID_LOCATION" });
    if (!options.geocoder) return reply.code(503).send({ error: "GEOCODING_UNAVAILABLE" });
    try {
      return await options.geocoder.resolve(query);
    } catch {
      return reply.code(404).send({
        error: "LOCATION_NOT_FOUND",
        message: "Try a more specific address or place name.",
      });
    }
  });

  app.get<{ Params: { placeId: string } }>(
    "/api/v1/places/:placeId/presentation",
    async (request, reply) => {
      reply.header("Cache-Control", "no-store");
      if (!/^[A-Za-z0-9_-]{1,200}$/.test(request.params.placeId))
        return reply.code(400).send({ message: "Invalid place identifier." });
      if (!options.presentation)
        return reply.code(503).send({ message: "Venue details are not configured." });
      try {
        return PlacePresentationSchema.parse(
          await options.presentation.place(request.params.placeId),
        );
      } catch {
        return reply
          .code(502)
          .send({ message: "Venue details could not be loaded. Please retry." });
      }
    },
  );
  app.get<{ Querystring: { name?: string; width?: string } }>(
    "/api/v1/place-photos",
    async (request, reply) => {
      reply.header("Cache-Control", "no-store");
      const name = PhotoResourceSchema.safeParse(request.query.name);
      const width = Number(request.query.width ?? 640);
      if (!name.success || ![640, 1280].includes(width))
        return reply.code(400).send({ message: "Invalid photo request." });
      if (!options.presentation)
        return reply.code(503).send({ message: "Venue photos are not configured." });
      try {
        return reply.redirect(await options.presentation.photo(name.data, width), 302);
      } catch {
        return reply.code(502).send({ message: "This photo is unavailable." });
      }
    },
  );
  app.post("/api/v1/routes/preview", async (request, reply) => {
    reply.header("Cache-Control", "no-store");
    const input = RoutePreviewRequestSchema.safeParse(request.body);
    if (!input.success) return reply.code(400).send({ message: "Invalid route preview request." });
    if (!options.presentation)
      return reply.code(503).send({ message: "Route previews are not configured." });
    try {
      return RoutePreviewSchema.parse(await options.presentation.routes(input.data));
    } catch {
      return reply.code(502).send({ message: "The route could not be loaded. Please retry." });
    }
  });

  app.post("/api/v1/recommendations", async (request, reply) => {
    const parsed = RecommendationRequestSchema.safeParse(request.body);
    if (!parsed.success)
      return reply.code(400).send({
        error: "INVALID_REQUEST",
        issues: parsed.error.issues.map((issue) => ({
          path: issue.path.join("."),
          message: issue.message,
        })),
      });
    try {
      const response = RecommendationResponseSchema.parse(await options.workflow.run(parsed.data));
      repository.save(parsed.data, response);
      return response;
    } catch (error) {
      const detail = error instanceof Error ? `${error.name}: ${error.message}` : "Unknown error";
      console.error(`[recommendation] ${detail}`);
      return reply.code(502).send({
        error: "RECOMMENDATION_FAILED",
        message: "The recommendation could not be generated.",
        ...(process.env.NODE_ENV !== "production" ? { detail } : {}),
      });
    }
  });
  app.get<{ Params: { requestId: string } }>(
    "/api/v1/recommendations/:requestId",
    async (request, reply) =>
      repository.find(request.params.requestId) ?? reply.code(404).send({ error: "NOT_FOUND" }),
  );
  if (options.enableDevRoutes)
    app.get("/api/dev/health", async () => ({
      status: "enabled",
      warning: "Development inspection routes are active.",
    }));
  return app;
}
