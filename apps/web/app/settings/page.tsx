"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Badge, Button, Card } from "@/components/ui";
import { theme } from "@/lib/theme";
import type { ProviderConfig } from "@/lib/types";

type ModelItem = {
  id: string;
  name: string;
  category: string;
  type: "cloud" | "local";
  size: string;
  status: "installed" | "not_installed" | "installing";
  progress: number;
  description: string;
};

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

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function SettingsPage() {
  const [configs, setConfigs] = useState<ProviderConfig[]>([]);
  const [models, setModels] = useState<ModelItem[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [ttsSelection, setTtsSelection] = useState<string>(defaults.tts!.provider_id);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [installingId, setInstallingId] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      try {
        const list = await api.listProjects();
        if (list && list.length > 0 && list[0]) {
          setProjectId(list[0].id);
        }
      } catch {
        // user not logged in
      }
    })();
  }, []);

  async function loadModels() {
    try {
      const res = await fetch(`${API_BASE}/models/status`);
      if (res.ok) {
        const data = await res.json();
        setModels(data.models ?? []);
      }
    } catch {
      // ignore offline error
    }
  }

  async function loadConfigs() {
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
    void loadModels();
    const interval = setInterval(loadModels, 2000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    void loadConfigs();
  }, [projectId]);

  async function installModel(modelId: string) {
    setInstallingId(modelId);
    try {
      const res = await fetch(`${API_BASE}/models/install`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model_id: modelId }),
      });
      if (res.ok) {
        setMessage(`🚀 Đã khởi chạy tiến trình tải & cài đặt mô hình ${modelId}`);
        await loadModels();
      }
    } catch (err) {
      setMessage(`❌ Lỗi cài đặt: ${String(err)}`);
    } finally {
      setInstallingId(null);
    }
  }

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
      await loadConfigs();
    } catch (exc) {
      setMessage(exc instanceof ApiError ? `Lỗi ${exc.status}` : String(exc));
    }
  }

  function configFor(kind: string): ProviderConfig | undefined {
    return configs.find((c) => c.provider_kind === kind);
  }

  return (
    <div style={{ padding: 24, maxWidth: 840, display: "flex", flexDirection: "column", gap: 20 }}>
      <header>
        <h1 style={{ margin: 0, fontSize: 22 }}>⚙️ Cài Đặt Cấu Hình & Quản Lý Mô Hình AI</h1>
        <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0" }}>
          Tải trực tiếp mô hình AI local (Qwen3, VietVoice, MeloTTS, UVR5) hoặc cấu hình Cloud Engines.
        </p>
      </header>

      {/* SECTION 1: ONE-CLICK MODEL INSTALLER */}
      <Card title="📦 Cài Đặt Mô Hình AI Trực Tiếp (1-Click Model Installer)">
        <div style={{ fontSize: 12, color: theme.textMuted, marginBottom: 12 }}>
          Các mô hình AI local có thể được tải & cài đặt trực tiếp từ Web App để chạy offline trên máy tính của bạn.
        </div>

        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {models.map((m) => (
            <div
              key={m.id}
              style={{
                padding: 12,
                background: theme.bgElevated,
                border: `1px solid ${theme.border}`,
                borderRadius: 8,
                display: "flex",
                alignItems: "center",
                gap: 12,
              }}
            >
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: 6,
                  background: theme.bgPanel,
                  display: "grid",
                  placeItems: "center",
                  fontSize: 18,
                }}
              >
                {m.type === "cloud" ? "☁️" : "📦"}
              </div>

              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <strong style={{ fontSize: 13 }}>{m.name}</strong>
                  <span style={{ fontSize: 11, color: theme.textMuted }}>({m.size})</span>
                </div>
                <div style={{ fontSize: 11, color: theme.textMuted, marginTop: 2 }}>{m.description}</div>

                {m.status === "installing" && (
                  <div style={{ marginTop: 6, width: "100%", maxWidth: 300 }}>
                    <div style={{ fontSize: 10, color: theme.accent, marginBottom: 2 }}>
                      Đang tải từ HuggingFace… {m.progress}%
                    </div>
                    <div style={{ height: 4, background: theme.bgPanel, borderRadius: 2, overflow: "hidden" }}>
                      <div style={{ width: `${m.progress}%`, height: "100%", background: theme.accent, transition: "width 200ms ease" }} />
                    </div>
                  </div>
                )}
              </div>

              <div>
                {m.status === "installed" ? (
                  <Badge tone="success">🟢 Sẵn sàng sử dụng</Badge>
                ) : m.status === "installing" ? (
                  <Badge tone="warn">⏳ Đang cài đặt {m.progress}%</Badge>
                ) : (
                  <Button
                    variant="primary"
                    size="sm"
                    disabled={installingId === m.id}
                    onClick={() => installModel(m.id)}
                  >
                    ⚡ Cài đặt ngay
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* SECTION 2: PROVIDER SELECTION */}
      <Card title="⚙️ Cấu Hình Engines Mặc Định (Provider Assignment)">
        <div style={{ display: "grid", gap: 14 }}>
          {kinds.map((kind) => {
            const cfg = configFor(kind.key);
            return (
              <div key={kind.key} style={{ padding: 12, background: theme.bgElevated, borderRadius: 6, border: `1px solid ${theme.border}` }}>
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <strong style={{ fontSize: 13 }}>{kind.label}</strong>
                  <Button size="sm" onClick={() => save(kind.key)}>
                    {cfg ? "Cập nhật" : "Lưu mặc định"}
                  </Button>
                </div>
                <div style={{ fontSize: 11, color: theme.textMuted, marginTop: 4 }}>
                  Engine đang kích hoạt: <strong style={{ color: theme.accent }}>{cfg ? cfg.provider_id : defaults[kind.key]?.provider_id}</strong>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {message && (
        <div style={{ color: theme.success, background: "#052e16", border: "1px solid #14532d", padding: 12, borderRadius: 6, fontSize: 13 }}>
          {message}
        </div>
      )}
    </div>
  );
}
