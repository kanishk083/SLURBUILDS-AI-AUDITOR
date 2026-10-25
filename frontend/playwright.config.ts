import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 240000,
  workers: 1,
  use: {
    baseURL: "http://localhost:3000",
    channel: "chrome",
    headless: true,
    viewport: { width: 1440, height: 1000 },
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
  },
  reporter: [
    ["list"],
    ["json", { outputFile: "../artifacts/browser-tests.json" }],
  ],
});
