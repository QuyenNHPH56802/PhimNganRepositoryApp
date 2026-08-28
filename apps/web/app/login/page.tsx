"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { loginStub } from "@web/lib/auth";
import { Button, Card, Input } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useT } from "@/lib/i18n";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { t } = useT();
  const [email, setEmail] = useState("ops@example.com");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await loginStub(API_BASE, email);
      const next = params.get("next") ?? "/projects";
      router.replace(next);
    } catch (exc) {
      setError((exc as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 12, minWidth: 320 }}>
      <p style={{ margin: 0, color: theme.textMuted, fontSize: 12 }}>{t("auth.loginHint", "Dev build: any email works")}</p>
      <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
        <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>{t("auth.email", "Email")}</span>
        <Input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      {error && (
        <div style={{ background: "#450a0a", color: theme.danger, padding: 8, borderRadius: 6, fontSize: 12 }}>
          {error}
        </div>
      )}
      <Button variant="primary" disabled={busy} type="submit">
        {busy ? t("common.loading", "Đang tải…") : t("auth.loginButton", "Đăng nhập")}
      </Button>
    </form>
  );
}

export default function LoginPage() {
  const { t } = useT();
  return (
    <div style={{ padding: 24, display: "grid", placeItems: "center", minHeight: "100%" }}>
      <Card title={t("auth.loginTitle", "Đăng nhập")} padded>
        <Suspense fallback={<div style={{ color: theme.textMuted, fontSize: 12 }}>{t("common.loading", "Đang tải…")}</div>}>
          <LoginForm />
        </Suspense>
      </Card>
    </div>
  );
}
