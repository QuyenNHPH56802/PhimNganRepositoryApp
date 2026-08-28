"use client";

import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import { loadToken } from "./auth";

export type AdminRole = "OWNER" | "EDITOR" | "VIEWER";

export function useAdminRole(): AdminRole | null {
  const [role, setRole] = useState<AdminRole | null>(null);
  useEffect(() => {
    if (!loadToken()) {
      setRole(null);
      return;
    }
    api
      .listProjects()
      .then(() => setRole("OWNER"))
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) {
          setRole(null);
          return;
        }
        setRole("VIEWER");
      });
  }, []);
  return role;
}
