import { NextRequest, NextResponse } from "next/server";
import { loadToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";

export async function GET(request: NextRequest) {
  const token = loadToken();
  const { searchParams } = new URL(request.url);
  const projectId = searchParams.get("project_id");

  try {
    const url = `${API_BASE_URL}/admin/voice-profiles${projectId ? `?project_id=${projectId}` : ""}`;
    const res = await fetch(url, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (!res.ok) {
      return NextResponse.json({ error: `HTTP ${res.status}` }, { status: res.status });
    }

    const data = await res.json();
    return NextResponse.json(data);
  } catch (err) {
    return NextResponse.json({ error: "Failed to fetch voice profiles" }, { status: 502 });
  }
}
