import { createAnthropic } from "@ai-sdk/anthropic";
import { createGoogleGenerativeAI } from "@ai-sdk/google";
import { createOpenAI } from "@ai-sdk/openai";
import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import type { LanguageModel } from "ai";

export type AgentName = "discovery" | "planning";
export type SupportedProvider = "openai" | "anthropic" | "google" | "openai-compatible";
export type Environment = Record<string, string | undefined>;
export interface LlmConfig {
  provider: SupportedProvider;
  model: string;
  apiKey: string;
  baseURL?: string;
  structuredOutputs: boolean;
}

function read(env: Environment, key: string): string {
  return env[key]?.trim() ?? "";
}
function providerKey(provider: string, env: Environment): string {
  if (provider === "openai") return read(env, "OPENAI_API_KEY");
  if (provider === "anthropic") return read(env, "ANTHROPIC_API_KEY");
  if (provider === "google") return read(env, "GOOGLE_API_KEY");
  return "";
}

export function resolveAgentConfig(agent: AgentName, env: Environment = process.env): LlmConfig {
  const prefix = agent.toUpperCase();
  const configuredProvider = read(env, `${prefix}_LLM_PROVIDER`) || read(env, "LLM_PROVIDER");
  const rawProvider = configuredProvider === "google_genai" ? "google" : configuredProvider;
  const model = read(env, `${prefix}_LLM_MODEL`) || read(env, "LLM_MODEL");
  const apiKey =
    read(env, `${prefix}_LLM_API_KEY`) || read(env, "LLM_API_KEY") || providerKey(rawProvider, env);
  const baseURL = read(env, `${prefix}_LLM_BASE_URL`) || read(env, "LLM_BASE_URL");
  const structuredSetting =
    read(env, `${prefix}_LLM_STRUCTURED_OUTPUTS`) || read(env, "LLM_STRUCTURED_OUTPUTS");
  const structuredOutputs = structuredSetting
    ? structuredSetting === "true"
    : baseURL.includes("api.nvidia.com");
  const supported = new Set<SupportedProvider>([
    "openai",
    "anthropic",
    "google",
    "openai-compatible",
  ]);
  if (!supported.has(rawProvider as SupportedProvider))
    throw new Error(`Unsupported LLM_PROVIDER: ${rawProvider || "missing"}`);
  if (!model) throw new Error(`LLM_MODEL is required for ${agent}`);
  if (!apiKey && !(rawProvider === "openai-compatible" && baseURL.includes("127.0.0.1")))
    throw new Error(`LLM_API_KEY is required for ${agent}`);
  if (rawProvider === "openai-compatible" && !baseURL)
    throw new Error("LLM_BASE_URL is required for openai-compatible providers");
  return {
    provider: rawProvider as SupportedProvider,
    model,
    apiKey: apiKey || "not-used",
    structuredOutputs,
    ...(baseURL ? { baseURL } : {}),
  };
}

export function createLanguageModel(config: LlmConfig): LanguageModel {
  switch (config.provider) {
    case "openai":
      return createOpenAI({
        apiKey: config.apiKey,
        ...(config.baseURL ? { baseURL: config.baseURL } : {}),
      })(config.model);
    case "anthropic":
      return createAnthropic({
        apiKey: config.apiKey,
        ...(config.baseURL ? { baseURL: config.baseURL } : {}),
      })(config.model);
    case "google":
      return createGoogleGenerativeAI({
        apiKey: config.apiKey,
        ...(config.baseURL ? { baseURL: config.baseURL } : {}),
      })(config.model);
    case "openai-compatible":
      return createOpenAICompatible({
        name: "configured",
        apiKey: config.apiKey,
        baseURL: config.baseURL!,
        supportsStructuredOutputs: config.structuredOutputs,
      })(config.model);
  }
}
