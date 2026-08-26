"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";

import { loginStub } from "@web/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

export default function LoginPage() {
  const router = useRouter();
  const params = useSearchParams();
  const [email, setEmail] = useState("ops@example.com");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await loginStub(API_BASE, email);
      const next = params.get("next") ?? "/";
      router.replace(next);
    } catch (exc) {
      setError((exc as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <section style={{ maxWidth: 360 }}>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Sign in</h1>
      <p style={{ color: "#94a3b8", marginBottom: 16 }}>
        Phase 4 stub. Production wires Google/Azure AD/Authentik OIDC.
      </p>
      <form onSubmit={handleSubmit}>
        <label style={{ display: "block", marginBottom: 8 }}>Email</label>
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          style={{ width: "100%", padding: 8, marginBottom: 12 }}
          required
        />
        <button type="submit" disabled={busy} style={{ padding: "8px 16px" }}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
        {error && <p style={{ color: "#f87171", marginTop: 12 }}>{error}</p>}
      </form>
    </section>
  );
}