import { test, expect } from "@playwright/test";
import fs from "node:fs";
test("private demo -> indexed sources -> real audit -> citation -> history -> mobile", async ({
  page,
}) => {
  fs.mkdirSync("../artifacts", { recursive: true });
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Every claim needs evidence." }),
  ).toBeVisible();
  await page.screenshot({
    path: "../artifacts/welcome-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Open workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "Follow the evidence." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "New library", exact: true }).click();
  await page.getByLabel("Library name").fill("Audit practice");
  await page
    .getByRole("button", { name: "Create library", exact: true })
    .click();
  await expect(page.getByLabel("Reference library")).toContainText(
    "Audit practice",
  );
  await page.getByRole("button", { name: "Load sample" }).click();
  await expect(
    page.getByRole("button", { name: "Audit answer", exact: true }),
  ).toBeEnabled({ timeout: 120000 });
  await page.getByRole("button", { name: "Audit answer", exact: true }).click();
  await expect(page.locator(".report-summary")).toBeVisible({
    timeout: 180000,
  });
  await expect(page.locator(".summary-number")).toHaveText(["2", "2", "2"]);
  await expect(page.locator(".claim")).toHaveCount(6);
  await page.screenshot({
    path: "../artifacts/audit-desktop.png",
    fullPage: true,
  });
  await page.locator(".citation").first().click();
  await expect(
    page.getByRole("dialog", { name: "Source evidence" }),
  ).toBeVisible();
  await expect(page.getByRole("dialog").getByRole("blockquote")).toContainText(
    "199",
  );
  await page.screenshot({
    path: "../artifacts/source-desktop.png",
    fullPage: true,
  });
  await page.getByRole("button", { name: "Close source" }).click();
  await page
    .getByRole("button", { name: "Audit history", exact: true })
    .click();
  await expect(page.locator(".history-list>button")).toHaveCount(1);
  await page.locator(".history-list>button").first().click();
  await expect(page.locator(".report-summary")).toBeVisible();
  await page
    .getByRole("button", { name: "Compare methods", exact: true })
    .click();
  await page.getByLabel("Research lab").selectOption("graph");
  await page.getByRole("button", { name: "Run lab", exact: true }).click();
  await expect(page.locator(".lab-result pre")).toContainText("nodes", {
    timeout: 60000,
  });
  await page
    .getByRole("button", { name: "Run fixture evaluation", exact: true })
    .click();
  await expect(page.locator(".evaluation-table tbody tr")).toHaveCount(3, {
    timeout: 180000,
  });
  await page.screenshot({
    path: "../artifacts/experiments-desktop.png",
    fullPage: true,
  });
  await page
    .getByRole("button", { name: "Audit workspace", exact: true })
    .click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../artifacts/audit-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  expect(errors).toEqual([]);
});
