"use client";

import { useEditor } from "@/lib/store";
import { Button, Card, EmptyState, Input, Select } from "@/components/ui";
import { speakerColor, theme } from "@/lib/theme";

export function SpeakerPanel() {
  const speakers = useEditor((s) => s.speakers);
  const voices = useEditor((s) => s.voices);
  const renameSpeaker = useEditor((s) => s.renameSpeaker);
  const assignSpeakerToVoice = useEditor((s) => s.assignSpeakerToVoice);

  if (speakers.length === 0) {
    return (
      <EmptyState
        title="Chưa có speaker"
        description="Chạy bước Diarization để nhận diện speaker trong audio."
      />
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      {speakers.map((sp, idx) => (
        <Card key={sp.id} padded>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 40,
                height: 40,
                borderRadius: 999,
                background: speakerColor(idx),
                display: "grid",
                placeItems: "center",
                fontWeight: 700,
                color: "#0b1220",
              }}
            >
              {sp.label.charAt(0).toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <Input
                value={sp.label}
                onChange={(e) => renameSpeaker(sp.id, e.target.value)}
              />
              <div style={{ fontSize: 11, color: theme.textMuted, marginTop: 4 }}>
                Gender: {sp.gender ?? "unknown"} • ID: {sp.id.slice(0, 8)}
              </div>
            </div>
            <Select
              value={sp.voice_profile_id ?? ""}
              onChange={(e) => assignSpeakerToVoice(sp.id, e.target.value || null)}
              style={{ maxWidth: 200 }}
            >
              <option value="">— Voice —</option>
              {voices.map((v) => (
                <option key={v.id} value={v.id}>{v.name}</option>
              ))}
            </Select>
            <Button>Preview</Button>
          </div>
        </Card>
      ))}
    </div>
  );
}
