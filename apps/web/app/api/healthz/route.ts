import { NextResponse } from "next/server";
import { API_BASE_URL } from "@/lib/types";

// Aggregate health: probe the backend's /healthz and /readyz in parallel and
// surface a single payload. Returns 200 only when both succeed.
export async function GET(): Promise<NextResponse> {
  const [healthz, readyz] = await Promise.allSettled([
    fetch(`${API_BASE_URL}/healthz`, { cache: "no-store" }),
    fetch(`${API_BASE_URL}/readyz`, { cache: "no-store" }),
  ]);

  const probe = (r: PromiseSettledResult<Response>, name: string) => {
    if (r.status === "fulfilled" && r.value.ok) {
      return { status: r.value.status, ok: true };
    }
    const reason =
      r.status === "rejected"
        ? r.reason instanceof Error
          ? r.reason.message
          : String(r.reason)
        : `HTTP ${"value" in r ? r.value?.status ?? "?" : "?"}`;
    return { status: "value" in r ? r.value?.status ?? 0 : 0, ok: false, error: reason, name };
  };

  const body = {
    healthz: probe(healthz, "healthz"),
    readyz: probe(readyz, "readyz"),
    ok:
      healthz.status === "fulfilled" &&
      healthz.value.ok &&
      readyz.status === "fulfilled" &&
      readyz.value.ok,
    // Build identity — exposed so the EnvBadge can show "development · abc1234"
    // without an extra round trip. Safe to expose (no secrets).
    env: process.env.NEXT_PUBLIC_APP_ENV ?? process.env.NODE_ENV ?? "development",
    sha: process.env.NEXT_PUBLIC_GIT_SHA ?? "",
    build: process.env.NEXT_PUBLIC_BUILD_ID ?? "",
  };

  return NextResponse.json(body, { status: body.ok ? 200 : 503 });
}