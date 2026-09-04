"use client";

import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import { Button, Card } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useT } from "@/lib/i18n";
import type { VoiceProfile } from "@/lib/types";

const CONSENT_LABELS: Record<string, string> = {
  granted: "Đã đồng ý",
  denied: "Từ chối",
  pending: "Chờ xác nhận",
};

export default function VoicePage() {
  const { t } = useT();
  const [items, setItems] = useState<VoiceProfile[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function load() {
    setBusy(true);
    setError(null);
    try {
      const profiles = await api.listAdminVoiceProfiles();
      setItems(profiles);
    } catch (exc) {
      setError(exc instanceof ApiError ? exc.message : String(exc));
    } finally {
      setBusy(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>Hồ sơ Giọng đọc & Đồng ý (Voice Consent)</h1>
          <p style={{ margin: "6px 0 0", color: theme.textMuted, fontSize: 13 }}>
            Quản lý danh sách giọng đọc tiếng Việt và xác nhận quyền sử dụng từ người nói.
          </p>
        </div>
        <Button onClick={() => void load()}>{t("common.retry", "Tải lại danh sách")}</Button>
      </header>

      <Card title={t("voice.profiles", "Danh sách Giọng đọc trong hệ thống")} padded={false}>
        {busy && <div style={{ padding: 16, color: theme.textMuted, fontSize: 13 }}>{t("common.loading", "Đang tải…")}</div>}
        {error && (
          <div style={{ padding: 16, color: theme.danger, fontSize: 13 }}>
            Lỗi: {error}
          </div>
        )}
        {!busy && !error && items.length === 0 && (
          <div style={{ padding: 28, color: theme.textMuted, fontSize: 13, textAlign: "center" }}>
            Chưa có voice profile nào trong hệ thống. Tạo dự án và chạy workflow để tạo giọng đọc tự động.
          </div>
        )}
        {items.length > 0 && (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#0d172e" }}>
                {["Speaker", "Project", "Consent", "Reference Audio", "Profile ID"].map((h) => (
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
              {items.map((p) => (
                <tr key={p.id} style={{ borderBottom: `1px solid ${theme.border}` }}>
                  <td style={{ padding: "10px 14px", fontWeight: 600, fontSize: 13 }}>
                    {p.speaker_id ? p.speaker_id.slice(0, 12) + "…" : <em style={{ color: theme.textMuted }}>Chưa gán</em>}
                  </td>
                  <td style={{ padding: "10px 14px", fontSize: 11, color: theme.textMuted, fontFamily: "monospace" }}>
                    {p.project_id.slice(0, 8)}…
                  </td>
                  <td style={{ padding: "10px 14px" }}>
                    <span
                      style={{
                        color: p.consent_status === "granted" ? theme.success : p.consent_status === "revoked" ? theme.danger : theme.warn,
                        fontWeight: 600,
                        fontSize: 12,
                      }}
                    >
                      {CONSENT_LABELS[p.consent_status ?? ""] ?? p.consent_status ?? "Chưa rõ"}
                    </span>
                  </td>
                  <td style={{ padding: "10px 14px", fontSize: 11, color: theme.textMuted, fontFamily: "monospace" }}>
                    {p.reference_audio_key ?? "—"}
                  </td>
                  <td style={{ padding: "10px 14px", fontSize: 11, color: theme.textMuted, fontFamily: "monospace" }}>
                    {p.id.slice(0, 8)}…
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
