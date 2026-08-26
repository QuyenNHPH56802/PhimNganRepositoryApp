import { test, expect } from "@playwright/test";

test.describe("Admin flow", () => {
  test("owner can switch quality mode and inspect audit log", async ({ page, request }) => {
    const login = await request.post("/api/auth/login", {
      data: { email: "owner@team", password: "owner-pass" },
    });
    expect(login.ok()).toBeTruthy();
    const cookies = login.headers()["set-cookie"] ?? "";
    await page.context().addCookies([
      { name: "session", value: cookies.split(";")[0].split("=")[1] ?? "", url: page.url() },
    ]);

    const projects = await request.get("/api/projects");
    const project = (await projects.json())[0];

    await page.goto(`/projects/${project.id}/quality-mode`);
    await page.getByRole("button", { name: "HIGH" }).click();
    await expect(page.locator("pre")).toContainText("\"asr_provider\"");

    await page.goto("/admin/audit");
    await page.getByPlaceholder("action").fill("quality_mode_set");
    await page.getByRole("button", { name: "Tải lại" }).click();
    await expect(page.locator("table tbody tr").first()).toBeVisible();
  });
});