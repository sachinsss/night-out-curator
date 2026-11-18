import { render, screen, waitFor } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { ItineraryDashboard } from "./ItineraryDashboard";
import { requestFixture, resultFixture, presentationFixture } from "./results.test-fixtures";
vi.mock("./ResultMap", () => ({
  ResultMap: () => <div aria-label="Itinerary route map">Map preview</div>,
}));
beforeEach(() =>
  vi.stubGlobal(
    "fetch",
    vi.fn(async (url: string) => ({
      ok: true,
      json: async () =>
        url.includes("routes/preview")
          ? { legs: [], warnings: ["Route unavailable"] }
          : presentationFixture,
    })),
  ),
);
afterEach(() => vi.unstubAllGlobals());
test("shows a numbered itinerary, selects a venue, and preserves selection across tabs", async () => {
  const reset = vi.fn();
  render(<ItineraryDashboard result={resultFixture} request={requestFixture} onReset={reset} />);
  expect(screen.getByRole("heading", { name: "Your Night Out Route" })).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "View details for Centrico" }));
  expect(screen.getByRole("heading", { name: "Centrico" })).toBeVisible();
  await userEvent.click(screen.getByRole("tab", { name: "Menu" }));
  expect(screen.getByRole("link", { name: /Visit venue website/ })).toHaveAttribute(
    "href",
    "https://example.com/menu",
  );
  await userEvent.click(screen.getByRole("tab", { name: "Itinerary" }));
  await userEvent.click(screen.getByRole("tab", { name: "Details" }));
  expect(screen.getByRole("heading", { name: "Centrico" })).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Edit plan" }));
  expect(reset).toHaveBeenCalledOnce();
});
test("loads route geometry once on demand and reports provisional route failures", async () => {
  render(<ItineraryDashboard result={resultFixture} request={requestFixture} onReset={vi.fn()} />);
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3));
  await userEvent.click(screen.getByRole("tab", { name: "Map" }));
  await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Route unavailable"));
  expect(screen.getByText("Provisional", { exact: true })).toBeVisible();
  await userEvent.click(screen.getByRole("tab", { name: "Itinerary" }));
  await userEvent.click(screen.getByRole("tab", { name: "Map" }));
  expect(fetch).toHaveBeenCalledTimes(4);
});
test("shows missing metadata without invented costs and keeps failed enrichment retryable", async () => {
  vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("Unavailable")));
  const result = structuredClone(resultFixture);
  result.itineraries[0]!.estimatedCostPerPerson = null;
  render(<ItineraryDashboard result={result} request={requestFixture} onReset={vi.fn()} />);
  expect(screen.getByText("Cost unavailable")).toBeVisible();
  expect(await screen.findAllByText("Photo details unavailable")).toHaveLength(3);
});
