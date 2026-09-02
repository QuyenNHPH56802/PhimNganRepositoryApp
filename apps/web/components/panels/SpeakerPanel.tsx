"use client";

import { useState } from "react";
import { useEditor } from "@/lib/store";
import { Button, Card, EmptyState, Input, Select } from "@/components/ui";
import { speakerColor, theme } from "@/lib/theme";
import { api } from "@/lib/api";
import { useToast } from "@/lib/toast";

export function SpeakerPanel() {
  const speakers = useEditor((s) => s.speakers);
  const voices = useEditor((s) => s.voices);
  const renameSpeaker = useEditor((s) => s.renameSpeaker);
  const assignSpeakerToVoice = useEditor((s) => s.assignSpeakerToVoice);
  const projectId = useEditor((s) => s.projectId);
  const { toast } = useToast();
  
  const [previewingId, setPreviewingId] = useState<string | null>(null);
  const [previewText, setPreviewText] = useState("Xin chào, đây là giọng nói mẫu.");

  const GENDER_LABELS: Record<string, string> = {
    male: "Nam",
    female: "Nữ",
    unknown: "Không xác định",
  };

  async function handlePreview(speakerId: string) {
    if (!projectId) return;
    
    const speaker = speakers.find((s) => s.id === speakerId);
    if (!speaker) return;
    
    const voiceId = speaker.voice_profile_id;
    if (!voiceId) {
      toast("Speaker này chưa được gán voice profile", "warn");
      return;
    }

    setPreviewingId(speakerId);
    try {
      const result = await api.previewVoice(projectId, voiceId, previewText);
      if (result?.audio_url) {
        window.open(result.audio_url, "_blank");
      } else {
        toast("Không có audio URL trả về", "warn");
      }
    } catch (err) {
      console.error("Preview failed:", err);
      toast("Không thể preview voice", "danger");
    } finally {
      setPreviewingId(null);
    }
  }

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
      {speakers.map((sp, idx) => {
        const voice = voices.find((v) => v.id === sp.voice_profile_id);
        
        return (
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
                  placeholder="Tên speaker"
                />
                <div style={{ fontSize: 11, color: theme.textMuted, marginTop: 4 }}>
                  Giới tính: {GENDER_LABELS[sp.gender ?? "unknown"]} •
                  ID: {sp.id.slice(0, 8)}
                  {voice && <span> • Voice: {voice.id.slice(0, 8)}</span>}
                </div>
              </div>
            </div>
            
            <div style={{ marginTop: 12 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>
                  Gán Voice:
                </span>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <Select
                  value={sp.voice_profile_id ?? ""}
                  onChange={(e) => assignSpeakerToVoice(sp.id, e.target.value || null)}
                  style={{ flex: 1 }}
                >
                  <option value="">— Chọn Voice —</option>
                  {voices.map((v) => (
                    <option key={v.id} value={v.id}>
                      {v.speaker_id ? `Speaker ${v.speaker_id.slice(0, 6)}` : `Voice ${v.id.slice(0, 8)}`}
                    </option>
                  ))}
                </Select>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={!sp.voice_profile_id || previewingId === sp.id}
                  onClick={() => handlePreview(sp.id)}
                  title={
                    !sp.voice_profile_id
                      ? "Gán voice profile cho speaker trước"
                      : "Nghe thử giọng nói"
                  }
                >
                  {previewingId === sp.id ? "..." : "▶"} Nghe thử
                </Button>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
