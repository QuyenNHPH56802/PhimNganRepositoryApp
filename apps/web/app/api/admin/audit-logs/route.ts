import { NextRequest, NextResponse } from "next/server";
import { hasToken, loadToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";

// Proxy GET /admin/audit-logs → backend, forwarding query params.
export async function GET(request: NextRequest): Promise<NextResponse> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (hasToken()) {
    const token = loadToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  const qs = request.nextUrl.searchParams.toString();
  const url = `${API_BASE_URL}/admin/audit-logs${qs ? `?${qs}` : ""}`;

  try {
    const res = await fetch(url, { method: "GET", headers, cache: "no-store" });

    const contentType = res.headers.get("content-type") ?? "";
    const payload = contentType.includes("application/json")
      ? await res.json().catch(() => null)
      : await res.text().catch(() => null);

    return NextResponse.json(payload ?? { items: [] }, { status: res.status });
  } catch (err) {
    return NextResponse.json({ error: "Không thể kết nối đến server" }, { status: 502 });
  }
}