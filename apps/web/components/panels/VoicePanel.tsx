"use client";

import { useState } from "react";
import { useEditor } from "@/lib/store";
import { Badge, Button, Card, EmptyState } from "@/components/ui";
import { theme } from "@/lib/theme";
import { api } from "@/lib/api";
import { useToast } from "@/lib/toast";
import { humanizeError } from "@/lib/errorMessage";

interface VoiceModalProps {
  voice?: {
    id: string;
    name?: string;
    provider_id?: string;
    model_id?: string;
  };
  onClose: () => void;
  onSave: (voice: any) => void;
}

const PROVIDER_OPTIONS = [
  { id: "edge-tts", name: "Microsoft Edge TTS", models: ["vi-VN-HoaiMyNeural", "vi-VN-NamMinhNeural"] },
  { id: "openai", name: "OpenAI TTS", models: ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] },
  { id: "cosyvoice", name: "Alibaba CosyVoice (Local GPU)", models: ["cosyvoice-300m-sft"] },
  { id: "qwen3_tts", name: "Alibaba Qwen3 TTS (Local GPU)", models: ["qwen3-tts-vc"] },
] as const;

function VoiceModal({ voice, onClose, onSave }: VoiceModalProps) {
  const isEdit = Boolean(voice?.id);
  const [name, setName] = useState(voice?.name ?? "");
  const [providerId, setProviderId] = useState(voice?.provider_id ?? "edge-tts");
  const [modelId, setModelId] = useState(voice?.model_id ?? "vi-VN-HoaiMyNeural");
  const [saving, setSaving] = useState(false);

  async function handleSave() {
    if (!name.trim()) {
      // Validation message stays as an alert-style warning so the user
      // notices before the modal closes.
      window.alert("Vui lòng nhập tên voice");
      return;
    }
    setSaving(true);
    try {
      onSave({ name, provider_id: providerId, model_id: modelId });
      onClose();
    } finally {
      setSaving(false);
    }
  }

  const currentProvider = PROVIDER_OPTIONS.find((p) => p.id === providerId);
  const models = currentProvider?.models ?? [];

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.7)",
        display: "grid",
        placeItems: "center",
        zIndex: 100,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: theme.bgElevated,
          borderRadius: 12,
          padding: 24,
          width: 400,
          border: `1px solid ${theme.border}`,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 style={{ margin: "0 0 16px", fontSize: 16 }}>
          {isEdit ? "Sửa Voice" : "Tạo Voice Mới"}
        </h3>

        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>Tên Voice</span>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="VD: Giọng Nam Việt"
              style={{
                background: theme.bgPanel,
                border: `1px solid ${theme.border}`,
                color: theme.text,
                padding: "8px 10px",
                borderRadius: 6,
                fontSize: 13,
                outline: "none",
              }}
            />
          </label>

          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>Provider</span>
            <select
              value={providerId}
              onChange={(e) => {
                setProviderId(e.target.value);
                const p = PROVIDER_OPTIONS.find((x) => x.id === e.target.value);
                if (p && p.models[0]) setModelId(p.models[0]);
              }}
              style={{
                background: theme.bgPanel,
                border: `1px solid ${theme.border}`,
                color: theme.text,
                padding: "8px 10px",
                borderRadius: 6,
                fontSize: 13,
                outline: "none",
              }}
            >
              {PROVIDER_OPTIONS.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>
          </label>

          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>Model</span>
            <select
              value={modelId}
              onChange={(e) => setModelId(e.target.value)}
              style={{
                background: theme.bgPanel,
                border: `1px solid ${theme.border}`,
                color: theme.text,
                padding: "8px 10px",
                borderRadius: 6,
                fontSize: 13,
                outline: "none",
              }}
            >
              {models.map((m) => (
                <option key={m} value={m}>{m}</option>
              ))}
            </select>
          </label>
        </div>

        <div style={{ display: "flex", gap: 8, marginTop: 20, justifyContent: "flex-end" }}>
          <Button variant="ghost" onClick={onClose}>Hủy</Button>
          <Button variant="primary" disabled={saving} onClick={handleSave}>
            {saving ? "Đang lưu..." : "Lưu"}
          </Button>
        </div>
      </div>
    </div>
  );
}

export function VoicePanel() {
  const voices = useEditor((s) => s.voices);
  const loadVoices = useEditor((s) => s.loadVoices);
  const projectId = useEditor((s) => s.projectId);
  const { toast } = useToast();
  
  const [showModal, setShowModal] = useState(false);
  const [editingVoice, setEditingVoice] = useState<any>(null);
  const [previewingId, setPreviewingId] = useState<string | null>(null);

  async function handleCreateVoice(voiceData: any) {
    if (!projectId) return;
    try {
      const result = await api.createVoiceProfile(projectId, voiceData);
      loadVoices([...voices, result]);
      toast("Đã tạo voice profile", "success");
    } catch (err) {
      toast(humanizeError(err, "Không thể tạo voice").title, "danger");
    }
  }

  async function handleUpdateVoice(voiceData: any) {
    if (!projectId) return;
    try {
      const updatedVoices = voices.map((v) => (v.id === editingVoice?.id ? { ...v, ...voiceData } : v));
      await api.saveVoices(projectId, updatedVoices);
      loadVoices(updatedVoices);
      toast("Đã cập nhật voice profile", "success");
    } catch (err) {
      toast(humanizeError(err, "Không thể cập nhật voice").title, "danger");
    }
  }

  async function handlePreview(voiceId: string) {
    if (!projectId) return;
    setPreviewingId(voiceId);
    try {
      const result = await api.previewVoice(projectId, voiceId);
      if (result?.audio_url) {
        window.open(result.audio_url, "_blank");
      } else {
        toast("Không có audio URL trả về", "warn");
      }
    } catch (err) {
      toast(humanizeError(err, "Không thể preview voice").title, "danger");
    } finally {
      setPreviewingId(null);
    }
  }

  if (voices.length === 0) {
    return (
      <EmptyState
        title="Chưa có voice profile"
        description="Tạo voice profile từ provider TTS hoặc clone từ giọng thật."
        action={
          <Button variant="primary" onClick={() => setShowModal(true)}>
            + Tạo voice
          </Button>
        }
      />
    );
  }

  return (
    <div>
      <div style={{ marginBottom: 12, display: "flex", justifyContent: "flex-end" }}>
        <Button variant="primary" onClick={() => { setEditingVoice(null); setShowModal(true); }}>
          + Tạo voice
        </Button>
      </div>
      
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
                <div style={{ fontWeight: 600, fontSize: 13 }}>
                  {v.speaker_id ? `Speaker ${v.speaker_id.slice(0, 6)}` : `Voice ${v.id.slice(0, 8)}`}
                </div>
                <div style={{ fontSize: 11, color: theme.textMuted }}>
                  {v.reference_audio_key ?? "Chưa có reference audio"}
                </div>
              </div>
            </div>
            <div style={{ display: "flex", gap: 6, marginTop: 10, flexWrap: "wrap" }}>
              <Badge tone={v.consent_status === "granted" ? "success" : "warn"}>
                {v.consent_status === "granted" ? "Đã đồng ý" : "Chưa đồng ý"}
              </Badge>
            </div>
            <div style={{ display: "flex", gap: 6, marginTop: 12 }}>
              <Button
                size="sm"
                disabled={previewingId === v.id}
                onClick={() => handlePreview(v.id)}
              >
                {previewingId === v.id ? "..." : "▶"} Nghe thử
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => { setEditingVoice(v); setShowModal(true); }}
              >
                Sửa
              </Button>
            </div>
          </Card>
        ))}
      </div>

      {showModal && (
        <VoiceModal
          voice={editingVoice}
          onClose={() => setShowModal(false)}
          onSave={editingVoice ? handleUpdateVoice : handleCreateVoice}
        />
      )}
    </div>
  );
}
