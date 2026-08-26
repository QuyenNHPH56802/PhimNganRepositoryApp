"use client";

import { useEffect, useState } from "react";

export type AdminRole = "OWNER" | "EDITOR" | "VIEWER";

export function useAdminRole(): AdminRole | null {
  const [role, setRole] = useState<AdminRole | null>(null);
  useEffect(() => {
    fetch("/api/me")
      .then((r) => r.json())
      .then((data) => setRole(data?.role ?? null))
      .catch(() => setRole(null));
  }, []);
  return role;
}