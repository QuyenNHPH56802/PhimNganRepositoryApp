"use client";

import { ReactNode } from "react";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAdminRole } from "@/lib/useAdminRole";

// Gates owner-only surfaces. In single-user mode every viewer is the owner
// so this is effectively a pass-through, but the hook is wired so a future
// multi-user flow will redirect non-owners automatically.
export function RequireOwner({ children }: { children: ReactNode }) {
  const role = useAdminRole();
  const router = useRouter();

  useEffect(() => {
    if (role !== "OWNER") {
      // Non-owners cannot reach the admin area; redirect to the dashboard.
      router.replace("/");
    }
  }, [role, router]);

  if (role !== "OWNER") return null;
  return <>{children}</>;
}
