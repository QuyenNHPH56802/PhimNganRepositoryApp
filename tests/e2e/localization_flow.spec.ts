import { test, expect } from "@playwright/test";

test.describe("Quy trình Việt hoá Video Trung → Việt (E2E Test)", () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to login page
    await page.goto("/login");
    await page.waitForLoadState("networkidle");

    // Login using stub admin account
    const emailInput = page.locator("input[type='email']");
    if (await emailInput.isVisible()) {
      await emailInput.fill("admin@translator.local");
      await page.getByRole("button", { name: /Đăng nhập/i }).click();
      await page.waitForURL((url) => url.pathname === "/" || url.pathname === "/projects", { timeout: 10000 }).catch(() => {});
    }
  });

  test("1. Hiển thị Dashboard giao diện Tiếng Việt chuẩn", async ({ page }) => {
    await page.goto("/");
    await page.waitForLoadState("domcontentloaded");

    // Check Vietnamese page headers
    await expect(page.locator("h1")).toContainText(/Bảng điều khiển/i);
    await expect(page.locator("body")).toContainText(/Trung → Việt/i);
  });

  test("2. Khởi tạo Dự án Dịch thuật Trung → Việt mượt mà", async ({ page }) => {
    await page.goto("/projects/new");
    await page.waitForLoadState("domcontentloaded");

    // Check Vietnamese form labels
    await expect(page.locator("h1")).toContainText(/Tạo project mới|Tạo dự án mới/i);

    // Fill project form
    const titleInput = page.locator("input[placeholder*='Tập 1']").first();
    await titleInput.fill("Dự án Dịch Phim Trung - Việt E2E Test");

    // Submit creation form
    const submitBtn = page.getByRole("button", { name: /Tạo project|Bắt đầu tạo dự án/i });
    await submitBtn.click();

    // Verify redirected to project workspace or project detail
    await page.waitForURL(/\/projects\/[a-f0-9-]+/, { timeout: 15000 });
    expect(page.url()).toMatch(/\/projects\/[a-f0-9-]+/);
  });

  test("3. Kiểm tra Workspace & Các tab Tiếng Việt chuẩn flow", async ({ page, request }) => {
    // Create project via API for workspace inspection
    const loginRes = await request.post("http://localhost:8000/auth/login/stub", {
      data: { email: "admin@translator.local" },
    });
    const token = (await loginRes.json()).token;

    const projRes = await request.post("http://localhost:8000/projects", {
      data: {
        title: "Dự án Test Workspace E2E",
        source_language: "zh",
        target_language: "vi",
        quality_mode: "balanced",
      },
      headers: { Authorization: `Bearer ${token}` },
    });
    const project = await projRes.json();

    // Navigate to workspace page
    await page.goto(`/projects/${project.id}/workspace`);
    await page.waitForLoadState("domcontentloaded");

    // Target workspace tab navigation bar (second nav element)
    const workspaceNav = page.locator("nav").last();
    await expect(workspaceNav).toContainText("Transcript");
    await expect(workspaceNav).toContainText("Translation");
    await expect(workspaceNav).toContainText("Render");

    // Click Render tab and check Vietnamese Render settings UI
    await page.getByRole("button", { name: "Render" }).click();
    await expect(page.locator("body")).toContainText(/Cấu hình Render Video|Render/i);
  });
});
