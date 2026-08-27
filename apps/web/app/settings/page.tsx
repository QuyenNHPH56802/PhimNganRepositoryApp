"use client";

import { useEffect, useState } from "react";

type ProviderConfig = {
  id: string;
  provider_kind: string;
  provider_id: string;
  config: Record<string, unknown>;
  is_active: boolean;
};

const kinds = [
  { key: "translate", label: "Translation" },
  { key: "qa", label: "Translation QA" },
  { key: "subtitle", label: "Subtitle" },
  { key: "tts", label: "TTS" },
  { key: "audio_separation", label: "Audio separation" },
  { key: "render", label: "Render" },
];

const ttsProviders = [
  { id: "edge_tts", label: "Edge TTS (free)", description: "Microsoft Edge neural voices, no API key required" },
  { id: "qwen3_tts", label: "Qwen3 TTS (high quality)", description: "Alibaba Qwen3, multilingual, requires GPU for local deployment" },
  { id: "vietvoice_tts", label: "VietVoice TTS", description: "Vietnamese-only local model; GPU recommended" },
  { id: "vieneu_v3_turbo", label: "VieNeu TTS", description: "Vietnamese voice-clone capable; GPU recommended" },
  { id: "cosyvoice_3", label: "CosyVoice 3", description: "Multilingual voice-clone capable; GPU required" },
  { id: "cloud_azure", label: "Azure TTS", description: "Commercial neural TTS (AZURE_TTS_KEY)" },
  { id: "cloud_google", label: "Google Cloud TTS", description: "Commercial neural TTS (GOOGLE_TTS_KEY)" },
  { id: "cloud_elevenlabs", label: "ElevenLabs", description: "Commercial neural TTS with voice cloning (ELEVENLABS_API_KEY)" },
  { id: "melotts_vi", label: "MeloTTS (VI)", description: "Lightweight Vietnamese local model" },
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
  const [ttsSelection, setTtsSelection] = useState<string>(defaults.tts.provider_id);

  async function load() {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    const res = await fetch(`${base}/projects/00000000-0000-0000-0000-000000000000/provider-configs`);
    if (res.ok) {
      const data = (await res.json()) as ProviderConfig[];
      setConfigs(data);
      const activeTts = data.find((c) => c.provider_kind === "tts" && c.is_active);
      if (activeTts) {
        setTtsSelection(activeTts.provider_id);
      }
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function save(kind: string, overrideProviderId?: string) {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    const fallback = defaults[kind];
    const providerId = overrideProviderId ?? fallback.provider_id;
    const body = {
      provider_kind: kind,
      provider_id: providerId,
      config: fallback.config,
      is_active: true,
    };
    const res = await fetch(`${base}/projects/00000000-0000-0000-0000-000000000000/provider-configs`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.ok) {
      setMessage(`Đã lưu provider cho ${kind}`);
      load();
    } else {
      setMessage(`Lỗi ${res.status}`);
    }
  }

  function configFor(kind: string): ProviderConfig | undefined {
    return configs.find((c) => c.provider_kind === kind);
  }

  function renderTtsSelector() {
    return (
      <div style={{ padding: 12, background: "#1e293b", borderRadius: 8 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <strong>TTS</strong>
          <button
            onClick={() => save("tts", ttsSelection)}
            style={{ background: "#0ea5e9", color: "#0f172a", border: 0, padding: "6px 12px", cursor: "pointer" }}
          >
            {configFor("tts") ? "Update" : "Save"}
          </button>
        </div>
        <label htmlFor="tts-provider-select" style={{ display: "block", marginTop: 8, color: "#cbd5f5", fontSize: 12 }}>
          Provider:
        </label>
        <select
          id="tts-provider-select"
          value={ttsSelection}
          onChange={(e) => setTtsSelection(e.target.value)}
          style={{
            marginTop: 4,
            width: "100%",
            padding: "8px",
            background: "#0f172a",
            color: "#f1f5f9",
            border: "1px solid #334155",
            borderRadius: 4,
          }}
        >
          {ttsProviders.map((p) => (
            <option key={p.id} value={p.id}>
              {p.label}
            </option>
          ))}
        </select>
        <p style={{ marginTop: 6, color: "#94a3b8", fontSize: 12 }}>
          {ttsProviders.find((p) => p.id === ttsSelection)?.description}
        </p>
        <pre style={{ marginTop: 8, padding: 8, background: "#0f172a", color: "#cbd5f5", fontSize: 12, overflow: "auto" }}>
          {(() => {
            const cfg = configFor("tts");
            return cfg ? JSON.stringify(cfg, null, 2) : "Not configured";
          })()}
        </pre>
      </div>
    );
  }

  return (
    <section style={{ maxWidth: 720 }}>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Provider Settings</h1>
      <p style={{ color: "#94a3b8" }}>Phase 3: lưu config vào API. Real workflow sẽ dùng config này cho từng project.</p>
      <div style={{ display: "grid", gap: 16, marginTop: 16 }}>
        {kinds.map((kind) => {
          if (kind.key === "tts") {
            return renderTtsSelector();
          }
          const cfg = configFor(kind.key);
          return (
            <div key={kind.key} style={{ padding: 12, background: "#1e293b", borderRadius: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>{kind.label}</strong>
                <button
                  onClick={() => save(kind.key)}
                  style={{ background: "#0ea5e9", color: "#0f172a", border: 0, padding: "6px 12px", cursor: "pointer" }}
                >
                  {cfg ? "Update" : "Save"}
                </button>
              </div>
              <pre style={{ marginTop: 8, padding: 8, background: "#0f172a", color: "#cbd5f5", fontSize: 12, overflow: "auto" }}>
                {cfg ? JSON.stringify(cfg, null, 2) : "Not configured"}
              </pre>
            </div>
          );
        })}
      </div>
      {message && <p style={{ color: "#7dd3fc", marginTop: 16 }}>{message}</p>}
    </section>
  );
}
