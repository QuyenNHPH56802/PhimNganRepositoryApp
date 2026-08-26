import { ReactNode } from "react";
import { useAdminRole } from "@/lib/useAdminRole";

export function RequireOwner({ children }: { children: ReactNode }) {
  const role = useAdminRole();
  if (role === null) {
    return <p className="text-gray-500">Đang tải…</p>;
  }
  if (role !== "OWNER") {
    return <p className="text-red-500">403 — yêu cầu role OWNER.</p>;
  }
  return <>{children}</>;
}