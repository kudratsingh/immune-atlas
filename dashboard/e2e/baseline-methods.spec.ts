import { expect, test } from "@playwright/test";

test("baseline page shows the Part 4 counts and the form aside", async ({ page }) => {
  await page.goto("/baseline/");
  await expect(page.getByText("656", { exact: true }).first()).toBeVisible();
  await expect(page.getByText("656 subjects")).toBeVisible();
  await expect(page.getByRole("region", { name: /By project/ }).getByText("384")).toBeVisible();
  await expect(page.getByRole("region", { name: /By sex/ }).getByText("344")).toBeVisible();
  await expect(page.getByText("10,206.15")).toBeVisible();
  await expect(page.getByText("485 samples", { exact: false }).first()).toBeVisible();
});

test("methods page shows provenance from the run report", async ({ page }) => {
  await page.goto("/methods/");
  await expect(page.getByText(/^011373475d/)).toBeVisible();
  await expect(page.getByRole("img", { name: /Database schema/ })).toBeVisible();
  await expect(page.getByText("Mann-Whitney U", { exact: false }).first()).toBeVisible();
});
