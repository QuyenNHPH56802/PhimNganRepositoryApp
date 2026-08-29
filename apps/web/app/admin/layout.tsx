"use client";

import { ReactNode } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { RequireOwner } from "@/components/RequireOwner";
import { theme } from "@/lib/theme";

const navItems = [
  { href: "/admin", label: "📊 Tổng quan Hệ thống", icon: "📊" },
  { href: "/admin/audit", label: "📜 Nhật ký Hệ thống (Audit Log)", icon: "📜" },
  { href: "/admin/voice", label: "🎙 Quản lý Giọng đọc (Voice Profiles)", icon: "🎙" },
  { href: "/admin/dataset", label: "🧪 Tập dữ liệu Kiểm định (Golden Dataset)", icon: "🧪" },
];

export default function AdminLayout({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <RequireOwner>
      <div style={{ display: "grid", gridTemplateColumns: "240px 1fr", minHeight: "100vh", background: theme.bg }}>
        <aside
          style={{
            background: theme.bgElevated,
            borderRight: `1px solid ${theme.border}`,
            padding: 16,
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <div style={{ paddingBottom: 12, borderBottom: `1px solid ${theme.border}` }}>
            <h2 style={{ fontSize: 15, margin: 0, color: theme.accent, fontWeight: 700 }}>
              ★ Trung tâm Quản trị
            </h2>
            <span style={{ fontSize: 11, color: theme.textMuted }}>Admin System Governance</span>
          </div>
          <nav style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            {navItems.map((item) => {
              const active = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "10px 12px",
                    borderRadius: 6,
                    fontSize: 13,
                    fontWeight: active ? 600 : 500,
                    color: active ? theme.accent : theme.text,
                    background: active ? "rgba(125,211,252,0.12)" : "transparent",
                    textDecoration: "none",
                    border: `1px solid ${active ? theme.border : "transparent"}`,
                  }}
                >
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </aside>
        <main style={{ padding: 24, minWidth: 0 }}>{children}</main>
      </div>
    </RequireOwner>
  );
}