import { describe, expect, it } from "vitest";
import { SqliteCache } from "./sqlite-cache.js";

describe("SqliteCache", () => {
  it("returns unexpired JSON and removes expired entries", () => {
    let now = 1_000;
    const cache = new SqliteCache(":memory:", () => now);
    cache.set("key", { value: 1 }, 100);
    expect(cache.get("key")).toEqual({ value: 1 });
    now = 1_101;
    expect(cache.get("key")).toBeNull();
    cache.close();
  });

  it("keeps provider and model cache keys isolated", () => {
    const cache = new SqliteCache(":memory:");
    const first = cache.createKey({
      agent: "planning",
      provider: "openai",
      model: "a",
      promptVersion: "1",
      schemaVersion: "1",
      input: { city: "Tempe" },
    });
    const second = cache.createKey({
      agent: "planning",
      provider: "anthropic",
      model: "a",
      promptVersion: "1",
      schemaVersion: "1",
      input: { city: "Tempe" },
    });
    expect(first).not.toBe(second);
    cache.close();
  });

  it("replaces a value atomically", () => {
    const cache = new SqliteCache(":memory:");
    cache.set("key", { version: 1 }, 1000);
    cache.set("key", { version: 2 }, 1000);
    expect(cache.get("key")).toEqual({ version: 2 });
    cache.close();
  });
});
