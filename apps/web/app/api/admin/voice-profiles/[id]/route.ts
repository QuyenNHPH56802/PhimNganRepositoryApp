import { NextRequest, NextResponse } from "next/server";
import { loadToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const token = loadToken();

  try {
    const res = await fetch(`${API_BASE_URL}/admin/voice-profiles/${id}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });

    if (!res.ok) {
      return NextResponse.json({ error: `HTTP ${res.status}` }, { status: res.status });
    }

    return NextResponse.json(await res.json());
  } catch (err) {
    return NextResponse.json({ error: "Failed to fetch voice profile" }, { status: 502 });
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  const { id } = params;
  const token = loadToken();

  try {
    const body = await request.json();
    const res = await fetch(`${API_BASE_URL}/admin/voice-profiles/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      return NextResponse.json({ error: `HTTP ${res.status}` }, { status: res.status });
    }

    return NextResponse.json(await res.json());
  } catch (err) {
    return NextResponse.json({ error: "Failed to update voice profile" }, { status: 502 });
  }
}
