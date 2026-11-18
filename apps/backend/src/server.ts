import { GoogleResultPresentation } from "./presentation/google-result-presentation.js";
import { config } from "dotenv";
import { mkdirSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { DiscoveryAgent } from "./agents/discovery-agent.js";
import { PlanningAgent } from "./agents/planning-agent.js";
import { buildApp } from "./app.js";
import { SqliteCache } from "./cache/sqlite-cache.js";
import { GoogleGeocoder } from "./integrations/geocoding/google-geocoder.js";
import { GooglePlacesClient } from "./integrations/places/google-places-client.js";
import { GoogleRoutesClient } from "./integrations/routes/google-routes-client.js";
import { GoogleWeatherClient } from "./integrations/weather/google-weather-client.js";
import { ValleyMetroRealtimeClient } from "./integrations/transit/valley-metro-realtime-client.js";
import { createLanguageModel, resolveAgentConfig } from "./llm/provider-factory.js";
import { AiSdkLlmClient } from "./llm/structured-client.js";
import { SqliteRecommendationRepository } from "./repositories/recommendation-repository.js";
import { RecommendationWorkflow } from "./workflows/recommendation-workflow.js";

config({ path: resolve(dirname(fileURLToPath(import.meta.url)), "../../../.env") });
const googleKey = process.env.GOOGLE_MAPS_API_KEY?.trim();
if (!googleKey) throw new Error("GOOGLE_MAPS_API_KEY is required");
const discoveryConfig = resolveAgentConfig("discovery");
const planningConfig = resolveAgentConfig("planning");
const databasePath = resolve(process.env.DATABASE_URL || "./data/night-out.sqlite");
mkdirSync(dirname(databasePath), { recursive: true });
const valleyMetroUrls = [
  process.env.VALLEY_METRO_TRIP_UPDATES_URL,
  process.env.VALLEY_METRO_ALERTS_URL,
]
  .map((value) => value?.trim())
  .filter((value): value is string => Boolean(value));
const transitRealtime = new ValleyMetroRealtimeClient(valleyMetroUrls);
const workflow = new RecommendationWorkflow({
  discoveryAgent: new DiscoveryAgent(new AiSdkLlmClient(createLanguageModel(discoveryConfig))),
  planningAgent: new PlanningAgent(new AiSdkLlmClient(createLanguageModel(planningConfig))),
  places: new GooglePlacesClient(googleKey),
  weather: new GoogleWeatherClient(googleKey),
  routes: new GoogleRoutesClient(googleKey, fetch, transitRealtime),
  cache: new SqliteCache(databasePath),
  cacheIdentities: { discovery: discoveryConfig, planning: planningConfig },
});
const frontendOrigin = process.env.FRONTEND_ORIGIN || "http://127.0.0.1:5173";
const host = process.env.HOST || "127.0.0.1";
const port = Number(process.env.PORT || 3000);
const app = buildApp({
  workflow,
  presentation: new GoogleResultPresentation(googleKey),
  geocoder: new GoogleGeocoder(googleKey),
  repository: new SqliteRecommendationRepository(databasePath),
  enableDevRoutes:
    process.env.NODE_ENV !== "production" && process.env.ENABLE_DEV_ROUTES !== "false",
  frontendOrigin,
});
await app.listen({ host, port });
console.info(`Backend ready: http://${host}:${port}`);
console.info(`Health check: http://${host}:${port}/api/v1/health`);
console.info(`Frontend: ${frontendOrigin}`);
