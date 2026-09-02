import { NextRequest, NextResponse } from "next/server";
import { hasToken, loadToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";

// Proxy POST /admin/datasets/sentences → backend
export async function POST(request: NextRequest): Promise<NextResponse> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (hasToken()) {
    const token = loadToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  try {
    const res = await fetch(`${API_BASE_URL}/admin/datasets/sentences`, {
      method: "POST",
      headers,
      body: JSON.stringify(body),
    });

    const contentType = res.headers.get("content-type") ?? "";
    const payload = contentType.includes("application/json")
      ? await res.json().catch(() => null)
      : await res.text().catch(() => null);

    return NextResponse.json(payload ?? { ok: res.ok }, { status: res.status });
  } catch (err) {
    return NextResponse.json({ error: "Không thể kết nối đến server" }, { status: 502 });
  }
}