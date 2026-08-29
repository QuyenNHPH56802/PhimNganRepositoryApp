"use client";

import { useEffect, useState } from "react";
import { loadToken } from "./auth";

export type AdminRole = "OWNER" | "EDITOR" | "VIEWER";

export function useAdminRole(): AdminRole | null {
  const [role, setRole] = useState<AdminRole | null>(null);

  useEffect(() => {
    const token = loadToken();
    if (token) {
      setRole("OWNER");
    } else {
      setRole(null);
    }
  }, []);

  return role;
}
