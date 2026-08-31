import { expect, test } from "@playwright/test";

test("response page shows the reference cohort and statistics", async ({ page }) => {
  await page.goto("/response/");
  await expect(page.getByText("1,968").first()).toBeVisible();
  await expect(page.getByText("Responders: 331 subjects / 993 samples.")).toBeVisible();
  const statsRegion = page.getByRole("region", { name: /Response comparison statistics/ });
  await expect(statsRegion.getByText(".013").first()).toBeVisible();
  await expect(statsRegion.getByText(".067").first()).toBeVisible();
  await expect(page.getByText(/CD4 T cells differs/)).toBeVisible();
});

test("per-subject toggle switches the statistics to subject counts", async ({ page }) => {
  await page.goto("/response/");
  await page.getByRole("button", { name: "Per subject" }).click();
  await expect(
    page.getByRole("columnheader", { name: "Responder subjects", exact: true }),
  ).toBeVisible();
  const statsRegion = page.getByRole("region", { name: /Response comparison statistics/ });
  await expect(statsRegion.getByText(".012").first()).toBeVisible();
});

test("day facet runs the per-day comparison", async ({ page }) => {
  await page.goto("/response/");
  await page.getByRole("button", { name: "Day 7" }).click();
  await expect(page.getByRole("button", { name: "Per subject" })).toBeDisabled();
  const statsRegion = page.getByRole("region", { name: /Response comparison statistics/ });
  await expect(statsRegion.getByText(".030").first()).toBeVisible();
});
