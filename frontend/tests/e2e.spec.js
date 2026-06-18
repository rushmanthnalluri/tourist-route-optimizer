import { test, expect } from '@playwright/test';

test.describe('Tourist Route Planner E2E', () => {
  
  test.beforeEach(async ({ page }) => {
    await page.goto('/');
  });

  test('Scenario 1: Generate itinerary successfully', async ({ page }) => {
    
    await page.click('a[href="/co2"]');
    
    await page.click('button:has-text("Run ASTAR")');
    await expect(page.locator('text=Path found').first()).toBeVisible({ timeout: 15000 });
  });

  test('Scenario 2: Budget too low', async ({ page }) => {
    await page.click('a[href="/co2"]');
    
    const budgetInput = page.locator('input[type="number"]').first();
    await budgetInput.fill('1');

    await page.click('button:has-text("Run ASTAR")');
    await expect(page.locator('text=No path found').first()).toBeVisible({ timeout: 15000 });
  });

  test('Scenario 3: Invalid attraction / API Failure Handling', async ({ page }) => {
    
    await page.route('**/api/search/run', route => {
      route.fulfill({
        status: 422,
        contentType: 'application/json',
        body: JSON.stringify({ detail: "Invalid attraction" })
      });
    });

    await page.click('a[href="/co2"]');
    await page.click('button:has-text("Run ASTAR")');

    await expect(page.locator('text=Backend error').first()).toBeVisible({ timeout: 10000 });
  });

  test('Scenario 4: Time constraint exceeded', async ({ page }) => {
    await page.click('a[href="/co2"]');

    const maxTimeInput = page.locator('input[type="number"]').nth(1);
    await maxTimeInput.fill('1');

    await page.click('button:has-text("Run ASTAR")');
    await expect(page.locator('text=No path found').first()).toBeVisible({ timeout: 15000 });
  });

  test('Scenario 5: Weather changes recommendation', async ({ page }) => {
    await page.click('a[href="/co6"]');
    
    const weatherSelect = page.locator('select').nth(1);
    await weatherSelect.selectOption('rain');

    await page.click('button:has-text("Run Full Hybrid Pipeline")');
    await expect(page.locator('text=Hybrid done').first()).toBeVisible({ timeout: 20000 });
  });

  test('Scenario 6: Multi-goal route generation', async ({ page }) => {
    
    const birlaCard = page.locator('.card', { hasText: 'Birla Mandir' });
    await birlaCard.locator('button:has-text("+ Goal")').click();

    await page.click('a[href="/co2"]');
    await page.click('button:has-text("Run ASTAR")');
    await expect(page.locator('text=Path found').first()).toBeVisible({ timeout: 15000 });
  });

  test('Scenario 7: Empty result handling', async ({ page }) => {
    
    const golcondaCard = page.locator('.card', { hasText: 'Golconda Fort' });
    await golcondaCard.locator('button:has-text("Goal")').click();

    const chowmahallaCard = page.locator('.card', { hasText: 'Chowmahalla Palace' });
    await chowmahallaCard.locator('button:has-text("Goal")').click();

    const meccaCard = page.locator('.card', { hasText: 'Mecca Masjid' });
    await meccaCard.locator('button:has-text("Goal")').click();

    await page.click('a[href="/co2"]');
    
    await page.click('button:has-text("Run ASTAR")');
    await expect(page.locator('text=Select at least 1 goal').first()).toBeVisible({ timeout: 10000 });
  });

  test('Scenario 8: API failure handling (500 Error)', async ({ page }) => {
    await page.route('**/api/search/run', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({ message: "Internal server error" })
      });
    });

    await page.click('a[href="/co2"]');
    await page.click('button:has-text("Run ASTAR")');
    await expect(page.locator('text=Backend error').first()).toBeVisible({ timeout: 10000 });
  });

  test('Scenario 9: Rate limit handling (429 Error)', async ({ page }) => {
    await page.route('**/api/search/run', route => {
      route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({ message: "Too many requests" })
      });
    });

    await page.click('a[href="/co2"]');
    await page.click('button:has-text("Run ASTAR")');
    await expect(page.locator('text=Backend error').first()).toBeVisible({ timeout: 10000 });
  });

  test('Scenario 10: Full happy-path user journey', async ({ page }) => {
    
    await page.click('a[href="/co3"]');
    
    await expect(page.locator('.leaflet-container')).toBeVisible({ timeout: 10000 });
    
    await page.click('button:has-text("Min-Conflicts")');
    
    await page.click('button:has-text("Schedule Attractions")');
    
    await expect(page.locator('text=Schedule Found').first()).toBeVisible({ timeout: 10000 });

    await page.click('a[href="/co6"]');
    await page.click('button:has-text("Run Full Hybrid Pipeline")');
    await expect(page.locator('text=Hybrid done').first()).toBeVisible({ timeout: 20000 });
  });

});
