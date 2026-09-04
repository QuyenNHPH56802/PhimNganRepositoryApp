import { test, expect } from '@playwright/test';

const PAGES = [
  { path: '/', name: 'Home' },
  { path: '/projects', name: 'Projects List' },
  { path: '/projects/new', name: 'New Project' },
  { path: '/admin', name: 'Admin Dashboard' },
  { path: '/admin/audit', name: 'Admin Audit' },
  { path: '/admin/voice', name: 'Admin Voice' },
  { path: '/admin/dataset', name: 'Admin Dataset' },
  { path: '/voice', name: 'Voice Page' },
  { path: '/settings', name: 'Settings' },
];

for (const pageInfo of PAGES) {
  test(`page-level errors on ${pageInfo.name} (${pageInfo.path})`, async ({ page }) => {
    const pageErrors: string[] = [];
    
    page.on('pageerror', err => {
      pageErrors.push(err.message);
    });
    
    await page.goto(pageInfo.path, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    console.log(`Page errors on ${pageInfo.path}:`, pageErrors.length > 0 ? pageErrors : 'None');
    
    expect(pageErrors.length).toBe(0);
  });
}
