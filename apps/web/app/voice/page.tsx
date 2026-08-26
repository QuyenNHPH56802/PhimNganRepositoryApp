"use client";

import { useEffect, useState } from "react";

import { loadToken } from "@web/lib/auth";

interface VoiceProfile {
  id: string;
  display_name: string;
  consent_status: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

export default function VoicePage() {
  const [items, setItems] = useState<VoiceProfile[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const token = loadToken();
    if (!token) return;
    const response = await fetch(`${API_BASE}/voice-profiles`, {
      headers: { Authorization: `Bearer ${token}` },
      cache: "no-store",
    });
    if (!response.ok) {
      setError(`voice profile fetch failed: ${response.status}`);
      return;
    }
    const payload = (await response.json()) as { items: VoiceProfile[] };
    setItems(payload.items ?? []);
  }

  useEffect(() => {
    void load();
  }, []);

  async function setConsent(profileId: string, action: "grant" | "revoke") {
    const token = loadToken();
    if (!token) return;
    const response = await fetch(`${API_BASE}/voice-profiles/${profileId}/consent:${action}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ evidence_key: action === "grant" ? "tos-signed" : "user-request" }),
    });
    if (response.ok) await load();
  }

  return (
    <section>
      <h1 style={{ fontSize: 22, marginBottom: 12 }}>Voice consent</h1>
      {error && <p style={{ color: "#f87171" }}>{error}</p>}
      <ul>
        {items.map((profile) => (
          <li key={profile.id} style={{ marginBottom: 8 }}>
            <strong>{profile.display_name}</strong> — status: {profile.consent_status}
            <button
              onClick={() => setConsent(profile.id, "grant")}
              style={{ marginLeft: 8, padding: "2px 8px" }}
            >
              Grant
            </button>
            <button
              onClick={() => setConsent(profile.id, "revoke")}
              style={{ marginLeft: 4, padding: "2px 8px" }}
            >
              Revoke
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}