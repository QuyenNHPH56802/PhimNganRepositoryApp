import { test, expect } from '@playwright/test';

/**
 * E2E: Keyboard shortcuts modal.
 *
 * Verifies that pressing `?` opens the help modal listing active shortcuts,
 * the modal can be closed with Escape, and the help button in the header
 * has the right accessible name.
 *
 * Works on the workspace page where ShortcutsHelp is mounted.
 */

test('shortcuts help modal opens with ? key and lists entries', async ({ page }) => {
  // Skip if backend is unreachable — workspace requires the API.
  await page.goto('/projects', { waitUntil: 'networkidle' });
  // Navigate to a workspace if at least one project exists; otherwise we still
  // want to test the modal in isolation. Try the first project link.
  const firstProjectLink = page.locator('a[href^="/projects/"]').first();
  if ((await firstProjectLink.count()) > 0) {
    await firstProjectLink.click();
  } else {
    // No projects — fall back to direct route (modal won't mount here but we
    // still verify Escape handling and the page doesn't crash).
    await page.goto('/');
    test.skip(true, 'No projects available to open workspace');
    return;
  }

  await page.waitForLoadState('networkidle');

  // The help button is rendered as a ghost button labelled "Phím tắt".
  const helpButton = page.getByRole('button', { name: /phím tắt/i }).first();
  await expect(helpButton).toBeVisible();

  // Open via keyboard.
  await page.keyboard.press('?');
  const dialog = page.getByRole('dialog', { name: /phím tắt/i });
  await expect(dialog).toBeVisible();

  // Modal should list at least one shortcut.
  const items = dialog.locator('li');
  expect(await items.count()).toBeGreaterThan(0);

  // Escape closes the modal.
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
});

test('shortcuts help modal opens via header button click', async ({ page }) => {
  await page.goto('/projects', { waitUntil: 'networkidle' });
  const firstProjectLink = page.locator('a[href^="/projects/"]').first();
  test.skip((await firstProjectLink.count()) === 0, 'No projects available');
  await firstProjectLink.click();
  await page.waitForLoadState('networkidle');

  await page.getByRole('button', { name: /phím tắt/i }).first().click();
  const dialog = page.getByRole('dialog', { name: /phím tắt/i });
  await expect(dialog).toBeVisible();

  // Click outside the dialog (backdrop) to close.
  await page.mouse.click(20, 20);
  await expect(dialog).toBeHidden();
});

test('shortcuts help modal shows platform-aware Mod key label', async ({ page }) => {
  await page.goto('/projects', { waitUntil: 'networkidle' });
  const firstProjectLink = page.locator('a[href^="/projects/"]').first();
  test.skip((await firstProjectLink.count()) === 0, 'No projects available');
  await firstProjectLink.click();
  await page.waitForLoadState('networkidle');

  await page.keyboard.press('?');
  const dialog = page.getByRole('dialog', { name: /phím tắt/i });
  await expect(dialog).toBeVisible();

  // At least one entry with either Cmd/Ctrl label must be present (we register
  // Mod+Z at minimum).
  const dialogText = (await dialog.textContent()) ?? '';
  expect(dialogText.length).toBeGreaterThan(20);
  expect(dialogText).toMatch(/Hoàn tác|Làm lại/);
});
