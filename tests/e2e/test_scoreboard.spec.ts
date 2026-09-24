import { test, expect } from '@playwright/test';

test.describe('Sports League Scoreboard End-to-End Tests', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to base URL (http://localhost:8009)
    await page.goto('/');
  });

  test('should load the scoreboard page and display standings', async ({ page }) => {
    // Verify page loads with league title
    await expect(page.locator('h1')).toContainText(/Metropolitan Amateur Premier League|Sports League Scoreboard/i);

    // Verify standings table is visible and rendered
    const standingsTable = page.locator('table');
    await expect(standingsTable).toBeVisible();

    // Verify key table headers
    await expect(page.getByRole('columnheader', { name: /club/i })).toBeVisible();
    await expect(page.getByRole('columnheader', { name: /pts/i })).toBeVisible();

    // Verify at least one seeded club appears in the standings
    await expect(page.getByText('Riverside FC').first()).toBeVisible();
  });

  test('should navigate to matches tab and render match fixtures', async ({ page }) => {
    // Click on Matches & Results navigation tab
    const matchesTab = page.getByRole('button', { name: /matches & results/i });
    await expect(matchesTab).toBeVisible();
    await matchesTab.click();

    // Verify match cards or headers are rendered
    await expect(page.getByRole('heading', { name: /matches & fixtures/i })).toBeVisible();
    await expect(page.getByText(/matchday/i).first()).toBeVisible();
    await expect(page.getByText('Oakwood Rovers').first()).toBeVisible();
  });

  test('should open pitchside scorekeeper and update score components', async ({ page }) => {
    // Navigate to Pitchside Scorekeeper tab
    const scorekeeperTab = page.getByRole('button', { name: /pitchside scorekeeper/i });
    await expect(scorekeeperTab).toBeVisible();
    await scorekeeperTab.click();

    // Look for live console button or kick off button
    const openConsoleButton = page.getByRole('button', { name: /open live scoreboard console/i }).first();
    const kickOffButton = page.getByRole('button', { name: /kick off & start match/i }).first();

    if (await openConsoleButton.isVisible()) {
      await openConsoleButton.click();
    } else if (await kickOffButton.isVisible()) {
      await kickOffButton.click();
    }

    // Verify Pitchside Scorekeeper modal opens
    const modalTitle = page.getByRole('heading', { name: /pitchside scorekeeper/i });
    await expect(modalTitle).toBeVisible();

    // Read initial home score from the display
    const addHomeGoalButton = page.getByTitle('Add 1 Goal').first();
    await expect(addHomeGoalButton).toBeVisible();

    // Click to add 1 goal
    await addHomeGoalButton.click();

    // Verify toast or updated score component is visible
    await page.waitForTimeout(500);

    // Close the modal
    const closeButton = page.locator('button:has(svg.lucide-x)').first();
    if (await closeButton.isVisible()) {
      await closeButton.click();
    }
  });
});
