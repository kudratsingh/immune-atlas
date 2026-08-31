import { expect, test } from "@playwright/test";

test("overview shows the dataset shape and study structure", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("3,500").first()).toBeVisible();
  await expect(page.getByText("10,500").first()).toBeVisible();
  await expect(page.getByRole("heading", { name: "Study structure" })).toBeVisible();
});

test("samples page filters the Part 3 cohort down to its reference size", async ({ page }) => {
  await page.goto("/samples/?condition=melanoma&treatment=miraclib&sample_type=PBMC");
  await expect(page.getByText("1,968 of 10,500 samples match")).toBeVisible();
  await expect(page.getByRole("button", { name: "Download CSV" })).toBeEnabled();
});

test("samples long view shows the exact Part 2 columns", async ({ page }) => {
  await page.goto("/samples/");
  await page.getByRole("button", { name: "Long table" }).click();
  for (const column of ["sample", "total_count", "population", "count", "percentage"]) {
    await expect(page.getByRole("columnheader", { name: column, exact: true })).toBeVisible();
  }
});
