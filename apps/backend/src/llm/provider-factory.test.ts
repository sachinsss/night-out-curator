import { describe, expect, it } from "vitest";
import { resolveAgentConfig } from "./provider-factory.js";
const base = { LLM_PROVIDER: "openai", LLM_MODEL: "fast-model", LLM_API_KEY: "secret" };
describe("resolveAgentConfig", () => {
  it.each(["openai", "anthropic", "google"])("supports %s", (provider) =>
    expect(resolveAgentConfig("discovery", { ...base, LLM_PROVIDER: provider }).provider).toBe(
      provider,
    ),
  );
  it("supports provider-specific key fallbacks", () =>
    expect(
      resolveAgentConfig("discovery", {
        LLM_PROVIDER: "google",
        LLM_MODEL: "gemini",
        GOOGLE_API_KEY: "google-key",
      }).apiKey,
    ).toBe("google-key"));
  it("accepts google_genai as a Google provider alias", () =>
    expect(
      resolveAgentConfig("discovery", {
        LLM_PROVIDER: "google_genai",
        LLM_MODEL: "gemini",
        GOOGLE_API_KEY: "google-key",
      }).provider,
    ).toBe("google"));
  it("supports an OpenAI-compatible endpoint", () =>
    expect(
      resolveAgentConfig("discovery", {
        ...base,
        LLM_PROVIDER: "openai-compatible",
        LLM_BASE_URL: "https://nim.example/v1",
      }).provider,
    ).toBe("openai-compatible"));
  it("enables structured outputs for NVIDIA NIM", () =>
    expect(
      resolveAgentConfig("discovery", {
        ...base,
        LLM_PROVIDER: "openai-compatible",
        LLM_BASE_URL: "https://integrate.api.nvidia.com/v1",
      }).structuredOutputs,
    ).toBe(true));
  it("applies agent-specific overrides", () =>
    expect(
      resolveAgentConfig("planning", {
        ...base,
        PLANNING_LLM_PROVIDER: "anthropic",
        PLANNING_LLM_MODEL: "planner",
        PLANNING_LLM_API_KEY: "planner-key",
      }),
    ).toMatchObject({ provider: "anthropic", model: "planner", apiKey: "planner-key" }));
  it("requires a base URL for compatible providers", () =>
    expect(() =>
      resolveAgentConfig("discovery", { ...base, LLM_PROVIDER: "openai-compatible" }),
    ).toThrow("LLM_BASE_URL"));
  it("does not expose keys in errors", () => {
    try {
      resolveAgentConfig("discovery", {
        ...base,
        LLM_PROVIDER: "unsupported",
        LLM_API_KEY: "never-print-this",
      });
    } catch (error) {
      expect(String(error)).toContain("Unsupported LLM_PROVIDER");
      expect(String(error)).not.toContain("never-print-this");
    }
  });
});
