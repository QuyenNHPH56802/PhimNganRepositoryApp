import { NextRequest, NextResponse } from "next/server";
import { hasToken, loadToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";

export async function POST(
  request: NextRequest,
  { params }: { params: { id: string } },
): Promise<NextResponse> {
  const { id } = params;
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (hasToken()) {
    const token = loadToken();
    if (token) headers.Authorization = `Bearer ${token}`;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/workflows/${id}/cancel`, {
      method: "POST",
      headers,
    });

    // Pass the upstream status code through so the FE can branch on it
    // (e.g. show "feature not supported" only when the backend returns 404).
    let detail: unknown = null;
    const contentType = res.headers.get("content-type") ?? "";
    try {
      detail = contentType.includes("application/json") ? await res.json() : await res.text();
    } catch {
      detail = null;
    }

    return NextResponse.json(detail ?? { ok: res.ok }, { status: res.status });
  } catch (err) {
    return NextResponse.json(
      { error: "Không thể kết nối đến server" },
      { status: 502 },
    );
  }
}