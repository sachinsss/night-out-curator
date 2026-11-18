import { describe, expect, it } from "vitest";
import { extractJsonObject } from "./structured-client.js";
describe("extractJsonObject", () => {
  it("extracts fenced JSON", () =>
    expect(extractJsonObject('```json\n{"ok":true}\n```')).toEqual({ ok: true }));
  it("rejects responses without an object", () =>
    expect(() => extractJsonObject("no json here")).toThrow("JSON object"));
});
