"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import clsx from "clsx";
import { theme } from "@/lib/theme";
import { loadToken, clearToken, fetchSessionUser } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";
import type { SessionUser } from "@/lib/auth";
import { useT, SUPPORTED_LOCALES as I18N_LOCALES, LOCALE_LABELS } from "@/lib/i18n";

function useNavItems() {
  const { t } = useT();
  return [
    { href: "/", label: t("nav.dashboard", "Bảng điều khiển"), icon: "▣" },
    { href: "/projects", label: t("nav.projects", "Dự án"), icon: "▤" },
    { href: "/voice", label: t("nav.voices", "Giọng nói"), icon: "♪" },
    { href: "/settings", label: t("nav.settings", "Cài đặt"), icon: "⚙" },
    { href: "/admin", label: t("nav.admin", "Quản trị"), icon: "★" },
  ];
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { t, locale, setLocale } = useT();
  const navItems = useNavItems();
  const [user, setUser] = useState<SessionUser | null>(null);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setHydrated(true);
    let mounted = true;
    fetchSessionUser(API_BASE_URL).then((u) => {
      if (mounted) setUser(u);
    });
    return () => {
      mounted = false;
    };
  }, []);

  const isLoggedIn = hydrated && !!user;

  return (
    <div style={{ display: "flex", minHeight: "100vh", background: theme.bg, color: theme.text }}>
      <aside
        style={{
          width: 240,
          background: theme.bgElevated,
          borderRight: `1px solid ${theme.border}`,
          display: "flex",
          flexDirection: "column",
          position: "sticky",
          top: 0,
          height: "100vh",
          flexShrink: 0,
        }}
      >
        <div
          style={{
            padding: "16px 18px",
            borderBottom: `1px solid ${theme.border}`,
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <div
            style={{
              width: 30,
              height: 30,
              borderRadius: 6,
              background: `linear-gradient(135deg, ${theme.accentStrong}, #6366f1)`,
              display: "grid",
              placeItems: "center",
              fontWeight: 800,
              color: "#0b1220",
            }}
          >
            中
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <strong style={{ fontSize: 14 }}>{t("app.title", "China → VNE")}</strong>
            <span style={{ fontSize: 11, color: theme.textMuted }}>{t("app.subtitle", "Video Localization")}</span>
          </div>
        </div>

        <nav style={{ padding: "12px 8px", flex: 1, overflowY: "auto" }}>
          {navItems.map((item) => {
            const active = pathname === item.href || (item.href !== "/" && pathname?.startsWith(item.href));
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx("translator-nav-item")}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "8px 12px",
                  marginBottom: 2,
                  borderRadius: 6,
                  fontSize: 13,
                  fontWeight: active ? 600 : 500,
                  color: active ? theme.accent : theme.text,
                  background: active ? "rgba(125,211,252,0.08)" : "transparent",
                  textDecoration: "none",
                  transition: "background 120ms ease",
                }}
                onMouseEnter={(e) => {
                  if (!active) (e.currentTarget as HTMLElement).style.background = "#16223e";
                }}
                onMouseLeave={(e) => {
                  if (!active) (e.currentTarget as HTMLElement).style.background = "transparent";
                }}
              >
                <span style={{ width: 18, textAlign: "center", opacity: 0.8 }}>{item.icon}</span>
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div style={{ padding: "12px 14px", borderTop: `1px solid ${theme.border}` }}>
          {isLoggedIn && user ? (
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <div
                style={{
                  width: 28,
                  height: 28,
                  borderRadius: 999,
                  background: theme.bgPanel,
                  border: `1px solid ${theme.border}`,
                  display: "grid",
                  placeItems: "center",
                  fontSize: 12,
                  fontWeight: 700,
                }}
              >
                {user.email.charAt(0).toUpperCase()}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div
                  style={{
                    fontSize: 12,
                    color: theme.text,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {user.email}
                </div>
                <button
                  onClick={() => {
                    clearToken();
                    setUser(null);
                    router.push("/login");
                  }}
                  style={{
                    background: "transparent",
                    border: "none",
                    color: theme.textMuted,
                    fontSize: 11,
                    cursor: "pointer",
                    padding: 0,
                    textAlign: "left",
                  }}
                >
                  {t("auth.signOut", "Đăng xuất")}
                </button>
              </div>
            </div>
          ) : (
            <Link
              href="/login"
              style={{
                display: "block",
                padding: "8px 12px",
                borderRadius: 6,
                background: theme.accentStrong,
                color: "#0b1220",
                textAlign: "center",
                fontSize: 13,
                fontWeight: 700,
                textDecoration: "none",
              }}
            >
              {t("auth.signIn", "Đăng nhập")}
            </Link>
          )}
        </div>
      </aside>

      <main style={{ flex: 1, minWidth: 0, display: "flex", flexDirection: "column" }}>
        <header
          style={{
            height: 52,
            borderBottom: `1px solid ${theme.border}`,
            background: theme.bgElevated,
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 24px",
            position: "sticky",
            top: 0,
            zIndex: 10,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <Breadcrumbs pathname={pathname ?? "/"} t={t} />
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <select
              value={locale}
              onChange={(e) => setLocale(e.target.value as typeof locale)}
              aria-label="Language"
              style={{
                background: theme.bgPanel,
                color: theme.text,
                border: `1px solid ${theme.border}`,
                borderRadius: 6,
                padding: "4px 8px",
                fontSize: 12,
                cursor: "pointer",
              }}
              title={t("app.language", "Ngôn ngữ")}
            >
              {I18N_LOCALES.map((code) => (
                <option key={code} value={code}>
                  {LOCALE_LABELS[code]}
                </option>
              ))}
            </select>
            <Link
              href="/projects/new"
              style={{
                background: theme.accentStrong,
                color: "#0b1220",
                padding: "6px 14px",
                borderRadius: 6,
                fontWeight: 700,
                fontSize: 13,
                textDecoration: "none",
              }}
            >
              {t("nav.newProject", "+ Dự án mới")}
            </Link>
          </div>
        </header>
        <div style={{ flex: 1, minHeight: 0, display: "flex", flexDirection: "column" }}>{children}</div>
      </main>
    </div>
  );
}

function Breadcrumbs({ pathname, t }: { pathname: string; t: (k: string, fb?: string) => string }) {
  const parts = pathname.split("/").filter(Boolean);
  if (parts.length === 0) return <span style={{ fontWeight: 600, fontSize: 14 }}>{t("nav.dashboard", "Bảng điều khiển")}</span>;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 13 }}>
      {parts.map((part, i) => (
        <span key={i} style={{ color: i === parts.length - 1 ? theme.text : theme.textMuted }}>
          {i > 0 && <span style={{ margin: "0 6px", color: theme.textDim }}>/</span>}
          {decodeURIComponent(part)}
        </span>
      ))}
    </div>
  );
}
