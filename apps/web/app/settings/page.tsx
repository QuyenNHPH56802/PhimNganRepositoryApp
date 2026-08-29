"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Button, Card } from "@/components/ui";
import { theme } from "@/lib/theme";
import type { ProviderConfig } from "@/lib/types";

const kinds = [
  { key: "translate", label: "Dịch thuật (Translation LLM)" },
  { key: "qa", label: "Kiểm định chất lượng (QA Rule Engine)" },
  { key: "subtitle", label: "Phụ đề (Subtitle Generator)" },
  { key: "tts", label: "Tổng hợp giọng nói (TTS Service)" },
  { key: "audio_separation", label: "Tách nhạc nền (Audio Separation)" },
  { key: "render", label: "Xuất video (FFmpeg Render)" },
];

const ttsProviders = [
  { id: "edge_tts", label: "Microsoft Edge TTS (Miễn phí)", description: "Giọng đọc Microsoft Edge Neural, nhanh, miễn phí" },
  { id: "dashscope_tts", label: "Alibaba DashScope Qwen3 (Cloud)", description: "Alibaba Qwen3, tự nhiên, đa ngôn ngữ" },
  { id: "qwen3_tts", label: "Qwen3 TTS (Local)", description: "Alibaba Qwen3 tự host, cần GPU" },
  { id: "vietvoice_tts", label: "VietVoice TTS", description: "Mô hình chuyên tiếng Việt" },
  { id: "vieneu_v3_turbo", label: "VieNeu TTS", description: "Hỗ trợ nhân bản giọng tiếng Việt" },
  { id: "cosyvoice_3", label: "CosyVoice 3", description: "Hỗ trợ voice-clone đa ngôn ngữ" },
  { id: "cloud_azure", label: "Azure TTS", description: "Dịch vụ thương mại Microsoft Azure" },
  { id: "cloud_google", label: "Google Cloud TTS", description: "Dịch vụ thương mại Google Cloud" },
  { id: "cloud_elevenlabs", label: "ElevenLabs", description: "Voice cloning thương mại cao cấp" },
  { id: "melotts_vi", label: "MeloTTS (VI)", description: "Mô hình siêu nhẹ cho tiếng Việt" },
];

const defaults: Record<string, { provider_id: string; config: Record<string, unknown> }> = {
  translate: { provider_id: "openai_compatible_http", config: { model_id: "gpt-4o-mini", temperature: 0.2 } },
  qa: { provider_id: "rule_based", config: { length_ratio_min: 1.0, length_ratio_max: 3.5 } },
  subtitle: { provider_id: "cps_wrapper", config: { target_cps: 15.0, max_chars_per_line: 42 } },
  tts: { provider_id: "edge_tts", config: { voice_id: "vi-VN-HoaiMyNeural", speed: 1.0 } },
  audio_separation: { provider_id: "uvr5_mdx", config: { model_id: "MDX23K" } },
  render: { provider_id: "ffmpeg_render", config: { crf: 20, preset: "medium", subtitle_mode: "soft" } },
};

export default function SettingsPage() {
  const [configs, setConfigs] = useState<ProviderConfig[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [ttsSelection, setTtsSelection] = useState<string>(defaults.tts!.provider_id);
  const [projectId, setProjectId] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const list = await api.listProjects();
        if (list && list.length > 0 && list[0]) {
          setProjectId(list[0].id);
        }
      } catch {
        // user not logged in — fall back to read-only state
      }
    })();
  }, []);

  async function load() {
    if (!projectId) return;
    try {
      const data = await api.listProviderConfigs(projectId);
      setConfigs(data);
      const activeTts = data.find((c) => c.provider_kind === "tts" && c.is_active);
      if (activeTts) {
        setTtsSelection(activeTts.provider_id);
      }
    } catch (exc) {
      if (exc instanceof ApiError) {
        setMessage(`Lỗi tải provider config: ${exc.status}`);
      }
    }
  }

  useEffect(() => {
    void load();
  }, [projectId]);

  async function save(kind: string, overrideProviderId?: string) {
    if (!projectId) return;
    const fallback = defaults[kind];
    if (!fallback) return;
    const providerId = overrideProviderId ?? fallback.provider_id;
    const body = {
      provider_kind: kind,
      provider_id: providerId,
      config: fallback.config,
      is_active: true,
    };
    try {
      await api.upsertProviderConfig(projectId, body);
      setMessage(`Đã lưu cấu hình provider cho ${kind}`);
      await load();
    } catch (exc) {
      setMessage(exc instanceof ApiError ? `Lỗi ${exc.status}` : String(exc));
    }
  }

  function configFor(kind: string): ProviderConfig | undefined {
    return configs.find((c) => c.provider_kind === kind);
  }

  function renderTtsSelector() {
    return (
      <Card title="Tổng hợp Giọng nói (TTS Provider Engine)">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <strong style={{ fontSize: 14 }}>Chọn Engine Giọng đọc mặc định</strong>
          <Button variant="primary" size="sm" onClick={() => save("tts", ttsSelection)}>
            {configFor("tts") ? "Cập nhật Engine" : "Lưu cấu hình"}
          </Button>
        </div>
        <label htmlFor="tts-provider-select" style={{ display: "block", marginTop: 12, color: theme.textMuted, fontSize: 12 }}>
          Provider TTS đang chọn:
        </label>
        <select
          id="tts-provider-select"
          value={ttsSelection}
          onChange={(e) => setTtsSelection(e.target.value)}
          style={{
            marginTop: 6,
            width: "100%",
            padding: "10px",
            background: theme.bgElevated,
            color: theme.text,
            border: `1px solid ${theme.border}`,
            borderRadius: 6,
            fontSize: 13,
          }}
        >
          {ttsProviders.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        <p style={{ marginTop: 8, color: theme.accent, fontSize: 12 }}>
          💡 {ttsProviders.find((p) => p.id === ttsSelection)?.description}
        </p>
      </Card>
    );
  }

  return (
    <div style={{ padding: 24, maxWidth: 780, display: "flex", flexDirection: "column", gap: 16 }}>
      <header>
        <h1 style={{ margin: 0, fontSize: 22 }}>Cài Đặt Cấu Hình Máy Chủ & Model AI</h1>
        <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0" }}>
          Cấu hình các provider AI (ASR, Dịch thuật LLM, TTS, Render) áp dụng cho dự án.
        </p>
      </header>
      <div style={{ display: "grid", gap: 16 }}>
        {kinds.map((kind) => {
          if (kind.key === "tts") {
            return <div key="tts-special">{renderTtsSelector()}</div>;
          }
          const cfg = configFor(kind.key);
          return (
            <Card key={kind.key} title={kind.label}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: 12, color: theme.textMuted }}>
                  Provider hiện tại: <strong style={{ color: theme.text }}>{cfg ? cfg.provider_id : defaults[kind.key]?.provider_id}</strong>
                </span>
                <Button size="sm" onClick={() => save(kind.key)}>
                  {cfg ? "Cập nhật" : "Lưu mặc định"}
                </Button>
              </div>
            </Card>
          );
        })}
      </div>
      {message && <div style={{ color: theme.success, background: "#052e16", padding: 10, borderRadius: 6, fontSize: 13 }}>{message}</div>}
    </div>
  );
}
