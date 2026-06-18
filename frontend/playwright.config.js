import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  testMatch: /.*\.spec\.js/,
  fullyParallel: true,
  retries: 0,
  workers: 1, 
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000',
      port: 8000,
      timeout: 10000,
      reuseExistingServer: true,
      cwd: '../',
    },
    {
      command: 'npm run dev',
      port: 5173,
      timeout: 10000,
      reuseExistingServer: true,
      cwd: './',
    }
  ]
});