"use client";

import { useEditor } from "@/lib/store";
import { Badge, Button, Card, EmptyState } from "@/components/ui";
import { theme } from "@/lib/theme";

export function VoicePanel() {
  const voices = useEditor((s) => s.voices);

  if (voices.length === 0) {
    return (
      <EmptyState
        title="Chưa có voice profile"
        description="Tạo voice profile từ provider TTS hoặc clone từ giọng thật."
        action={<Button variant="primary">+ Tạo voice</Button>}
      />
    );
  }

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 12 }}>
      {voices.map((v) => (
        <Card key={v.id} padded>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div
              style={{
                width: 36,
                height: 36,
                borderRadius: 6,
                background: theme.bgElevated,
                border: `1px solid ${theme.border}`,
                display: "grid",
                placeItems: "center",
                fontSize: 18,
              }}
            >
              ♪
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontWeight: 600, fontSize: 13 }}>{v.name}</div>
              <div style={{ fontSize: 11, color: theme.textMuted }}>
                {v.provider_id} • {v.model_id}
              </div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
            <Badge tone={v.consent_status === "granted" ? "success" : "warn"}>{v.consent_status}</Badge>
            {v.default_accent && <Badge tone="info">{v.default_accent}</Badge>}
          </div>
          <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
            <Button size="sm">▶ Preview</Button>
            <Button size="sm">Edit</Button>
          </div>
        </Card>
      ))}
    </div>
  );
}
