import { render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { expect, test } from "vitest";
import { MapsAction } from "./MapsAction";
import { resultFixture, requestFixture } from "./results.test-fixtures";
test("offers ordered transit legs rather than an unsupported multi-waypoint trip", async () => {
  render(
    <MapsAction
      stops={resultFixture.itineraries[0]!.stops}
      request={{ ...requestFixture, transportation: "transit" }}
    />,
  );
  await userEvent.click(screen.getByRole("button", { name: "Open in Maps" }));
  const links = screen.getAllByRole("link");
  expect(links).toHaveLength(2);
  const first = new URL(links[0]!.getAttribute("href")!);
  const second = new URL(links[1]!.getAttribute("href")!);
  expect(first.searchParams.get("origin_place_id")).toBe("place1");
  expect(first.searchParams.get("destination_place_id")).toBe("place2");
  expect(second.searchParams.get("origin_place_id")).toBe("place2");
  expect(second.searchParams.get("destination_place_id")).toBe("place3");
  expect(first.searchParams.get("travelmode")).toBe("transit");
  expect(first.searchParams.has("waypoints")).toBe(false);
});
