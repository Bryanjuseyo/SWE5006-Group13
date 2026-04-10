import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',

  // Each test file runs sequentially to avoid shared-state conflicts
  fullyParallel: false,
  workers: 1,

  // Generous timeout for CI / slow machines
  timeout: 60_000,
  expect: { timeout: 10_000 },

  // Retry once on failure (network flakes, timing)
  retries: 1,

  reporter: [['list'], ['html', { open: 'never' }]],

  use: {
    baseURL: 'http://localhost:5173',
    // Capture a trace only when a test fails after retries
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
