import {
  PlanningOutputSchema,
  type PlanningOutput,
  type RecommendationRequest,
  type Venue,
} from "@night-out/contracts";
import type { WeatherContext } from "../integrations/weather/weather-client.js";
import type { LlmClient } from "../llm/structured-client.js";

export interface PlanningInput {
  request: RecommendationRequest;
  venues: Venue[];
  weather: WeatherContext | null;
  failedChecks?: string[];
}
export interface PlanningAgentLike {
  run(input: PlanningInput): Promise<PlanningOutput>;
}

export class PlanningAgent implements PlanningAgentLike {
  static readonly promptVersion = "planning-v1";
  constructor(private readonly llm: LlmClient) {}

  async run(input: PlanningInput): Promise<PlanningOutput> {
    const result = await this.llm.generateStructured({
      instructions:
        "Create up to three distinct feasible itineraries. Select only supplied Place IDs, keep the requested stop count, respect budget and transport constraints, and never invent missing facts. Treat missing hours or prices as uncertainty, not confirmation.",
      input,
      schema: PlanningOutputSchema,
    });
    return result.output;
  }
}
