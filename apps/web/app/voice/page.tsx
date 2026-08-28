"use client";

import { useEffect, useState } from "react";

import { api, ApiError } from "@/lib/api";
import { Button, Card } from "@/components/ui";
import { useT } from "@/lib/i18n";

interface VoiceProfile {
  id: string;
  speaker_id: string;
  display_name: string;
  consent_status: string;
  reference_audio_key: string | null;
}

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
      <header>
        <h1 style={{ margin: 0, fontSize: 22 }}>{t("voice.title", "Voice consent")}</h1>
        <p style={{ margin: "6px 0 0", color: "#94a3b8", fontSize: 13 }}>
          {t("voice.subtitle", "Quản lý giọng nói và consent của speaker.")}
        </p>
      </header>

      <Card title={t("voice.profiles", "Hồ sơ giọng")} padded={false}>
        {busy && <div style={{ padding: 16, color: "#94a3b8", fontSize: 13 }}>{t("common.loading", "Đang tải…")}</div>}
        {error && (
          <div style={{ padding: 16, color: "#f87171", fontSize: 13 }}>
            {error}
          </div>
        )}
        {!busy && !error && items.length === 0 && (
          <div style={{ padding: 24, color: "#94a3b8", fontSize: 13, textAlign: "center" }}>
            {t("voice.empty", "Chưa có voice profile nào. Tạo project và chạy workflow trước.")}
          </div>
        )}
        {items.length > 0 && (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#0d172e" }}>
                {[t("voice.colSpeaker", "Speaker"), t("voice.colStatus", "Trạng thái"), t("voice.colReference", "Reference audio")].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: "left",
                      padding: "10px 14px",
                      fontSize: 11,
                      fontWeight: 600,
                      color: "#94a3b8",
                      textTransform: "uppercase",
                      letterSpacing: 0.5,
                      borderBottom: "1px solid #1f2a44",
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((p) => (
                <tr key={p.id} style={{ borderBottom: "1px solid #1f2a44" }}>
                  <td style={{ padding: "10px 14px" }}>{p.display_name || p.speaker_id}</td>
                  <td style={{ padding: "10px 14px" }}>{p.consent_status}</td>
                  <td style={{ padding: "10px 14px", color: "#94a3b8", fontSize: 12 }}>
                    {p.reference_audio_key ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Button variant="secondary" onClick={() => void load()}>
        {t("common.retry", "Tải lại")}
      </Button>
    </div>
  );
}
