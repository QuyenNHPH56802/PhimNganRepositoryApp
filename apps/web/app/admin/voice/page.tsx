"use client";

import { useEffect, useState } from "react";
import { Button, Card, Badge } from "@/components/ui";
import { theme } from "@/lib/theme";

type VoiceProfile = {
  id: string;
  project_id: string;
  speaker_id: string;
  consent_status: "pending" | "granted" | "revoked";
  reference_audio_key: string | null;
  consent_evidence_key: string | null;
  name?: string;
};

const STATUS_LABELS: Record<string, string> = {
  granted: "Đã đồng ý",
  denied: "Từ chối",
  pending: "Chờ xác nhận",
  revoked: "Đã thu hồi",
};

export default function VoiceAdminPage() {
  const [items, setItems] = useState<VoiceProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [transitioning, setTransitioning] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch(`/api/admin/voice-profiles`, {
        headers: { "Content-Type": "application/json" },
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setItems(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function transition(profile: VoiceProfile, next: "granted" | "revoked") {
    setTransitioning(profile.id);
    try {
      const evidence = window.prompt(
        next === "granted"
          ? "Nhập evidence key cho consent (BẮT BUỘC, vd: consent-record-2026-01-15.pdf):"
          : "Nhập lý do thu hồi:"
      );
      if (evidence === null) {
        // User cancelled the dialog — leave the profile unchanged.
        return;
      }
      if (next === "granted" && evidence.trim() === "") {
        setError("Evidence key là bắt buộc khi cấp quyền (consent_evidence_key không được để trống).");
        setTransitioning(null);
        return;
      }
      const res = await fetch(`/api/admin/voice-profiles/${profile.id}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          consent_status: next,
          consent_evidence_key: evidence.trim() || null,
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      await load();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setTransitioning(null);
    }
  }

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>🎙️ Quản lý Voice Profiles & Consent</h1>
          <p style={{ margin: "4px 0 0", color: theme.textMuted, fontSize: 13 }}>
            Xem và quản lý trạng thái đồng ý của người nói cho tất cả voice profiles trong hệ thống.
          </p>
        </div>
        <Button onClick={() => void load()} disabled={loading}>
          {loading ? "⏳ Đang tải…" : "🔄 Tải lại"}
        </Button>
      </header>

      {error && (
        <div
          style={{
            background: "#450a0a",
            color: theme.danger,
            padding: 12,
            borderRadius: 6,
            fontSize: 12,
            border: "1px solid #7f1d1d",
          }}
        >
          ❌ Lỗi: {error}
        </div>
      )}

      <Card title={`Danh sách Voice Profiles (${items.length})`} padded={false}>
        {loading ? (
          <div style={{ padding: 24, color: theme.textMuted, fontSize: 13 }}>Đang tải…</div>
        ) : items.length === 0 ? (
          <div style={{ padding: 28, color: theme.textMuted, fontSize: 13, textAlign: "center" }}>
            Chưa có voice profile nào trong hệ thống.
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#0d172e" }}>
                {["Tên / Speaker", "Project", "Trạng thái Consent", "Reference Audio", "Hành động"].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: "left",
                      padding: "10px 14px",
                      fontSize: 11,
                      fontWeight: 600,
                      color: theme.textMuted,
                      textTransform: "uppercase",
                      letterSpacing: 0.5,
                      borderBottom: `1px solid ${theme.border}`,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((profile) => (
                <tr key={profile.id} style={{ borderBottom: `1px solid ${theme.border}` }}>
                  <td style={{ padding: "10px 14px" }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>
                      {profile.name || profile.speaker_id || profile.id.slice(0, 8)}
                    </div>
                    <div style={{ fontSize: 11, color: theme.textMuted, marginTop: 2 }}>
                      ID: {profile.id.slice(0, 8)}…
                    </div>
                  </td>
                  <td style={{ padding: "10px 14px", fontSize: 11, color: theme.textMuted, maxWidth: 160, overflow: "hidden", textOverflow: "ellipsis" }}>
                    {profile.project_id}
                  </td>
                  <td style={{ padding: "10px 14px" }}>
                    <Badge
                      tone={
                        profile.consent_status === "granted"
                          ? "success"
                          : profile.consent_status === "revoked"
                            ? "danger"
                            : "warn"
                      }
                    >
                      {STATUS_LABELS[profile.consent_status] ?? profile.consent_status}
                    </Badge>
                  </td>
                  <td style={{ padding: "10px 14px", fontSize: 11, color: theme.textMuted }}>
                    {profile.reference_audio_key ?? "—"}
                  </td>
                  <td style={{ padding: "10px 14px" }}>
                    <div style={{ display: "flex", gap: 6 }}>
                      {profile.consent_status !== "granted" && (
                        <Button
                          size="sm"
                          variant="default"
                          disabled={transitioning === profile.id}
                          onClick={() => transition(profile, "granted")}
                          style={{ background: "#052e16", color: theme.success, borderColor: "#14532d" }}
                        >
                          ✅ Grant
                        </Button>
                      )}
                      {profile.consent_status !== "revoked" && (
                        <Button
                          size="sm"
                          variant="danger"
                          disabled={transitioning === profile.id}
                          onClick={() => transition(profile, "revoked")}
                        >
                          ❌ Revoke
                        </Button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
