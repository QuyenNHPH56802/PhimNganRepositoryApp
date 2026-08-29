"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { loginStub } from "@/lib/auth";
import { Button, Card, Input } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useT } from "@/lib/i18n";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { t } = useT();
  const [email, setEmail] = useState("admin@translator.local");
  const [displayName, setDisplayName] = useState("Quản trị viên (Admin)");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function performLogin(targetEmail: string, name?: string) {
    setBusy(true);
    setError(null);
    try {
      await loginStub(API_BASE, targetEmail);
      const next = params.get("next") ?? "/";
      router.replace(next);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : String(exc));
      setBusy(false);
    }
  }

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    await performLogin(email, displayName);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, width: 380, maxWidth: "100%" }}>
      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>Tên hiển thị</span>
          <Input
            type="text"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
            placeholder="VD: Nguyễn Văn A"
            required
          />
        </label>

        <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>Địa chỉ Email</span>
          <Input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="admin@translator.local"
            required
          />
        </label>

        {error && (
          <div style={{ background: "#450a0a", color: theme.danger, padding: 10, borderRadius: 6, fontSize: 12, border: "1px solid #7f1d1d" }}>
            ❌ Lỗi đăng nhập: {error}
          </div>
        )}

        <Button variant="primary" disabled={busy} type="submit">
          {busy ? "⏳ Đang xác thực…" : "🔐 Đăng nhập ngay"}
        </Button>
      </form>

      <div style={{ borderTop: `1px solid ${theme.border}`, paddingTop: 14, display: "flex", flexDirection: "column", gap: 8 }}>
        <span style={{ fontSize: 11, color: theme.textMuted, textAlign: "center", fontWeight: 600 }}>
          Đăng nhập nhanh 1-Click (Tài khoản thử nghiệm):
        </span>
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          <Button
            size="sm"
            type="button"
            onClick={() => {
              setEmail("admin@translator.local");
              setDisplayName("Quản trị viên Hệ thống");
              void performLogin("admin@translator.local", "Quản trị viên Hệ thống");
            }}
          >
            ★ Admin System
          </Button>
          <Button
            size="sm"
            type="button"
            onClick={() => {
              setEmail("translator@translator.local");
              setDisplayName("Chuyên viên Dịch thuật");
              void performLogin("translator@translator.local", "Chuyên viên Dịch thuật");
            }}
          >
            ✍ Translator Lead
          </Button>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  const { t } = useT();
  return (
    <div style={{ padding: 24, display: "grid", placeItems: "center", minHeight: "100vh", background: theme.bg }}>
      <Card title="🔐 Đăng nhập vào Translator Platform" padded>
        <Suspense fallback={<div style={{ color: theme.textMuted, fontSize: 12, padding: 20 }}>Đang tải form đăng nhập…</div>}>
          <LoginForm />
        </Suspense>
      </Card>
    </div>
  );
}
