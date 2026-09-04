"use client";

import { useEffect, useState } from "react";
import { loadToken } from "./auth";

export type AdminRole = "OWNER" | "EDITOR" | "VIEWER";

const ROLE_CACHE_KEY = "translator_admin_role";
const ROLE_CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutes

interface CachedRole {
  role: AdminRole;
  expiresAt: number;
}

function readCachedRole(): AdminRole | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.sessionStorage.getItem(ROLE_CACHE_KEY);
    if (!raw) return null;
    const parsed: CachedRole = JSON.parse(raw);
    if (parsed.expiresAt < Date.now()) return null;
    return parsed.role;
  } catch {
    return null;
  }
}

function writeCachedRole(role: AdminRole): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(
    ROLE_CACHE_KEY,
    JSON.stringify({ role, expiresAt: Date.now() + ROLE_CACHE_TTL_MS }),
  );
}

// Returns the role for the current user.
//
// In single-user mode (current backend, `apps/api/auth_dependency.py`), every
// request is implicitly the provisioned owner — there is no per-user role.
// We default to `"OWNER"` so the admin area renders. Once a multi-user flow
// ships this hook should call `GET /auth/me` (or decode the JWT claim) and
// cache the result in `sessionStorage` for `ROLE_CACHE_TTL_MS`.
export function useAdminRole(): AdminRole {
  const [role, setRole] = useState<AdminRole>(() => readCachedRole() ?? "OWNER");

  useEffect(() => {
    // No-op in single-user mode. When multi-user lands, this effect should:
    //   1. Call `/auth/me` (or decode the token).
    //   2. setRole(resolvedRole); writeCachedRole(resolvedRole);
    // The cached value is already read synchronously in the initializer
    // above, so first render is always correct for the cached case.
    const token = loadToken();
    if (!token) return; // single-user mode: keep OWNER
    // Future multi-user path — intentionally a no-op today.
  }, []);

  return role;
}

// `true` if the current user is allowed to see owner-only surfaces.
export function useIsOwner(): boolean {
  return useAdminRole() === "OWNER";
}
