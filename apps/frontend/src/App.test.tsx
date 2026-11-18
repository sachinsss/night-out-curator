import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { test, expect, vi } from "vitest";
import { App } from "./App";
import { resultFixture, presentationFixture } from "./results.test-fixtures";

test("resolves an address before submitting and displays API errors", async () => {
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ label: "Downtown Phoenix", latitude: 33.4484, longitude: -112.074 }),
      })
      .mockResolvedValueOnce({ ok: false, status: 502, json: async () => ({}) }),
  );
  render(<App />);
  await userEvent.type(
    screen.getByLabelText("Address, neighborhood, or landmark"),
    "Downtown Phoenix",
  );
  await userEvent.click(screen.getByRole("button", { name: "Date" }));
  await userEvent.click(screen.getByRole("button", { name: "Today" }));
  await userEvent.click(screen.getByRole("button", { name: /generate itinerary/i }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/could not build/i);
  expect(fetch).toHaveBeenCalledTimes(2);
});

test("shows transit preferences when public transit is selected", async () => {
  render(<App />);
  await userEvent.click(screen.getByRole("button", { name: "Public transit" }));
  expect(screen.getByRole("button", { name: "Public transit" })).toHaveAttribute(
    "aria-pressed",
    "true",
  );
  expect(screen.getByLabelText("Transit priority")).toBeVisible();
});

test("keeps planner fields visible without redundant navigation or review controls", async () => {
  render(<App />);
  expect(screen.getByLabelText("Date")).toBeVisible();
  expect(screen.getByLabelText("Dietary requirements")).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "4" }));
  await userEvent.click(screen.getByRole("button", { name: "Romantic" }));
  expect(screen.queryByRole("button", { name: /Review & generate/ })).not.toBeInTheDocument();
  expect(screen.queryByRole("navigation")).not.toBeInTheDocument();
  expect(screen.getByRole("button", { name: "Romantic" })).toHaveAttribute("aria-pressed", "true");
  expect(screen.getByLabelText("Date")).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Remove Italian cuisine" }));
  expect(screen.queryByRole("button", { name: "Remove Italian cuisine" })).not.toBeInTheDocument();
});

test("applies the prompt with Enter without submitting the planner", async () => {
  render(<App />);
  const apply = screen.getByRole("button", { name: "Use description as additional preferences" });
  expect(apply).toBeDisabled();
  await userEvent.type(
    screen.getByRole("textbox", { name: "Describe your ideal night" }),
    "Quiet rooftop dinner{Enter}",
  );
  expect(screen.getByLabelText("Additional preferences")).toHaveValue("Quiet rooftop dinner");
  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});

test("editing preserves the form and results, including after failed regeneration", async () => {
  let fail = false;
  const fetcher = vi.fn(async (url: string) => {
    if (url.includes("locations/resolve"))
      return {
        ok: true,
        json: async () => ({ label: "Phoenix, AZ", latitude: 33.4484, longitude: -112.074 }),
      };
    if (url.includes("recommendations"))
      return fail
        ? { ok: false, status: 502, json: async () => ({}) }
        : { ok: true, json: async () => resultFixture };
    return { ok: true, json: async () => presentationFixture };
  });
  vi.stubGlobal("fetch", fetcher);
  render(<App />);
  await userEvent.click(screen.getByRole("button", { name: "Date" }));
  await userEvent.click(screen.getByRole("button", { name: "Today" }));
  const chosenDate = screen.getByRole("button", { name: "Date" }).textContent;
  await userEvent.click(screen.getByRole("button", { name: /Generate Itinerary/ }));
  await userEvent.click(await screen.findByRole("button", { name: "View details for Centrico" }));
  expect(screen.getByRole("heading", { name: "Centrico" })).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Edit plan" }));
  expect(screen.getByRole("button", { name: "Date" })).toHaveTextContent(chosenDate!);
  await userEvent.type(screen.getByLabelText("Additional preferences"), "Late jazz");
  await userEvent.click(screen.getByRole("button", { name: "Back to results" }));
  expect(screen.getByRole("heading", { name: "Centrico" })).toBeVisible();
  expect(fetcher.mock.calls.filter(([url]) => url.includes("recommendations"))).toHaveLength(1);
  await userEvent.click(screen.getByRole("button", { name: "Edit plan" }));
  expect(screen.getByLabelText("Additional preferences")).toHaveValue("Late jazz");
  fail = true;
  await userEvent.click(screen.getByRole("button", { name: /Generate Itinerary/ }));
  expect(await screen.findByRole("alert")).toHaveTextContent(/could not build/i);
  await userEvent.click(screen.getByRole("button", { name: "Back to results" }));
  expect(screen.getByRole("heading", { name: "Centrico" })).toBeVisible();
});
