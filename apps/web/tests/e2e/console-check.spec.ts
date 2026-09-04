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
  test(`console errors on ${pageInfo.name} (${pageInfo.path})`, async ({ page }) => {
    const errors: string[] = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') {
        errors.push(msg.text());
      }
    });
    
    page.on('pageerror', err => {
      errors.push(err.message);
    });
    
    await page.goto(pageInfo.path, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);
    
    console.log(`Errors on ${pageInfo.path}:`, errors.length > 0 ? errors : 'None');
    
    if (errors.length > 0) {
      console.log('Console errors found:');
      errors.forEach((err, i) => console.log(`  ${i + 1}. ${err}`));
    }
    
    expect(errors.length).toBe(0);
  });
}
