import { test, expect } from '@playwright/test';

/**
 * E2E: Skeleton loading state.
 *
 * Verifies that the workspace page shows skeleton placeholders while the
 * first batch of panel data is being fetched, then transitions to either
 * populated panels or an empty state once data arrives.
 */

test('workspace shows skeleton placeholders during initial load', async ({ page }) => {
  // Throttle the API response so we can observe the skeleton state.
  await page.route('**/api/projects/*/transcript**', async (route) => {
    await new Promise((r) => setTimeout(r, 1500));
    await route.continue();
  });
  await page.route('**/api/projects/*/translation**', async (route) => {
    await new Promise((r) => setTimeout(r, 1500));
    await route.continue();
  });

  await page.goto('/projects', { waitUntil: 'networkidle' });
  const firstProjectLink = page.locator('a[href^="/projects/"]').first();
  test.skip((await firstProjectLink.count()) === 0, 'No projects available');
  await firstProjectLink.click();

  // The skeleton uses .skeleton-shimmer — assert at least one is visible while
  // the throttled requests are still in-flight.
  const skeleton = page.locator('.skeleton-shimmer').first();
  await expect(skeleton).toBeVisible({ timeout: 5000 });
});

test('projects list shows skeleton rows while fetching', async ({ page }) => {
  // Throttle the projects list endpoint.
  await page.route('**/api/projects**', async (route) => {
    await new Promise((r) => setTimeout(r, 1000));
    await route.continue();
  });

  await page.goto('/projects', { waitUntil: 'domcontentloaded' });

  // Skeleton rows must appear before the table renders.
  const skeletonRows = page.locator('.skeleton-shimmer');
  await expect(skeletonRows.first()).toBeVisible({ timeout: 5000 });
  expect(await skeletonRows.count()).toBeGreaterThanOrEqual(3);
});

test('workspace transitions from skeleton to content without errors', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (err) => errors.push(err.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text());
  });

  await page.goto('/projects', { waitUntil: 'networkidle' });
  const firstProjectLink = page.locator('a[href^="/projects/"]').first();
  test.skip((await firstProjectLink.count()) === 0, 'No projects available');
  await firstProjectLink.click();

  // Wait for the skeleton to disappear (data loaded or empty state rendered).
  await expect(page.locator('.skeleton-shimmer').first()).toBeHidden({ timeout: 15000 });

  // The page should not have produced any uncaught errors during the transition.
  expect(errors).toEqual([]);
});
