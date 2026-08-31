import { expect, test } from "@playwright/test";

test("home renders the data-aware dashboard shell", async ({ page }) => {
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Immune cell populations across a clinical trial dataset" }),
  ).toBeVisible();
  await expect(page.getByRole("navigation", { name: "Primary navigation" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Three questions" })).toBeVisible();
  await expect(
    page.getByRole("link", { name: "Do responders differ from non-responders on miraclib?" }),
  ).toBeVisible();
});
