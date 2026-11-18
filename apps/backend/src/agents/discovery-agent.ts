import {
  SearchPlanSchema,
  type RecommendationRequest,
  type SearchPlan,
} from "@night-out/contracts";
import type { LlmClient } from "../llm/structured-client.js";

export interface DiscoveryAgentLike {
  run(request: RecommendationRequest): Promise<SearchPlan>;
}

export class DiscoveryAgent implements DiscoveryAgentLike {
  static readonly promptVersion = "discovery-v1";
  constructor(private readonly llm: LlmClient) {}

  async run(request: RecommendationRequest): Promise<SearchPlan> {
    const result = await this.llm.generateStructured({
      instructions:
        "Translate the outing request into at most five concise Google Places queries. Use only place categories and preferences supported by the request. Do not invent venues or facts.",
      input: request,
      schema: SearchPlanSchema,
    });
    return result.output;
  }
}
