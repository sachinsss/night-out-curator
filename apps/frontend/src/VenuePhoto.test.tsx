import { fireEvent, render, screen } from "@testing-library/react";
import { userEvent } from "@testing-library/user-event";
import { expect, test } from "vitest";
import { VenuePhoto } from "./VenuePhoto";
import { presentationFixture } from "./results.test-fixtures";
test("gallery navigation loads the chosen image and preserves source attribution", async () => {
  render(<VenuePhoto photos={presentationFixture.photos} name="Venue" gallery />);
  expect(screen.getByRole("link", { name: "Venue photographer" })).toHaveAttribute(
    "href",
    "https://maps.google.com/contributor",
  );
  await userEvent.click(screen.getByRole("button", { name: "Next photo" }));
  expect(screen.getByRole("img")).toHaveAttribute("src", expect.stringContaining("photos%2Ftwo"));
  await userEvent.click(screen.getByRole("button", { name: "Previous photo" }));
  expect(screen.getByRole("img")).toHaveAttribute("src", expect.stringContaining("photos%2Fone"));
});
test("failed photos have local retry and a single photo has no gallery controls", async () => {
  render(<VenuePhoto photos={presentationFixture.photos.slice(0, 1)} name="Venue" gallery />);
  expect(screen.queryByRole("button", { name: "Next photo" })).not.toBeInTheDocument();
  fireEvent.error(screen.getByRole("img"));
  expect(screen.getByText("Photo unavailable")).toBeVisible();
  await userEvent.click(screen.getByRole("button", { name: "Retry photo" }));
  expect(screen.getByRole("img")).toBeInTheDocument();
});
