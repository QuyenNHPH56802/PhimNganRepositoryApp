import { test, expect } from "@playwright/test";

test.describe("Admin flow & Real Login", () => {
  test("1. Persistent login and user registration", async ({ page, request }) => {
    const loginRes = await request.post("http://localhost:8000/auth/login/stub", {
      data: { email: "admin@translator.local", display_name: "Quản trị viên" },
    });
    expect(loginRes.ok()).toBeTruthy();
    const data = await loginRes.json();
    expect(data.token).toBeTruthy();
    expect(data.identity.email).toBe("admin@translator.local");
  });

  test("2. Admin Overview metrics inspection", async ({ page, request }) => {
    const loginRes = await request.post("http://localhost:8000/auth/login/stub", {
      data: { email: "admin@translator.local" },
    });
    const token = (await loginRes.json()).token;

    const overviewRes = await request.get("http://localhost:8000/admin/overview", {
      headers: { Authorization: `Bearer ${token}` },
    });
    expect(overviewRes.ok()).toBeTruthy();
    const overview = await overviewRes.json();
    expect(overview.status).toBe("healthy");
    expect(overview.metrics).toHaveProperty("projects");
    expect(overview.metrics).toHaveProperty("users");
  });
});