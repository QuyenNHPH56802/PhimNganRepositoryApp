"use client";

import { ReactNode } from "react";
import Link from "next/link";
import { useAdminRole } from "@/lib/useAdminRole";
import { theme } from "@/lib/theme";
import { Button, Card } from "@/components/ui";

export function RequireOwner({ children }: { children: ReactNode }) {
  const role = useAdminRole();

  if (role === null) {
    return (
      <div style={{ padding: 40, textAlign: "center" }}>
        <Card title="Yêu cầu Đăng nhập Admin">
          <div style={{ padding: 20, display: "flex", flexDirection: "column", alignItems: "center", gap: 12 }}>
            <p style={{ color: theme.textMuted, fontSize: 14 }}>
              Bạn chưa đăng nhập hoặc phiên làm việc đã hết hạn. Vui lòng đăng nhập với tài khoản Quản trị viên để truy cập.
            </p>
            <Link href="/login">
              <Button variant="primary">🔐 Đăng nhập Quản trị viên</Button>
            </Link>
          </div>
        </Card>
      </div>
    );
  }

  return <>{children}</>;
}
