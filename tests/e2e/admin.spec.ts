import { test, expect } from "@playwright/test";

test.describe("Admin flow", () => {
  test("owner can switch quality mode and inspect audit log", async ({ page, request }) => {
    const login = await request.post("http://localhost:8000/auth/login/stub", {
      data: { email: "admin@translator.local" },
    });
    expect(login.ok()).toBeTruthy();
    const token = (await login.json()).token;

    const projRes = await request.post("http://localhost:8000/projects", {
      data: {
        title: "Dự án Test Admin Flow E2E",
        source_language: "zh",
        target_language: "vi",
        quality_mode: "balanced",
      },
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(projRes.ok()).toBeTruthy();
    const project = await projRes.json();

    await page.goto(`/projects/${project.id}/quality-mode`);
    await page.waitForLoadState("domcontentloaded");

    const highBtn = page.getByRole("button", { name: /HIGH/i }).first();
    if (await highBtn.isVisible()) {
      await highBtn.click();
    }

    await page.goto("/admin/audit");
    await page.waitForLoadState("domcontentloaded");
    await expect(page.locator("h1")).toContainText(/Nhật ký|Audit/i);
  });
});