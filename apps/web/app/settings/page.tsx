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

const defaults: Record<string, { provider_id: string; config: Record<string, unknown> }> = {
  translate: { provider_id: "openai_compatible_http", config: { model_id: "gpt-4o-mini", temperature: 0.2 } },
  qa: { provider_id: "rule_based", config: { length_ratio_min: 1.0, length_ratio_max: 3.5 } },
  subtitle: { provider_id: "cps_wrapper", config: { target_cps: 15.0, max_chars_per_line: 42 } },
  tts: { provider_id: "vietvoice_tts", config: { voice_id: "vietvoice-female-1", speed: 1.0 } },
  audio_separation: { provider_id: "uvr5_mdx", config: { model_id: "MDX23K" } },
  render: { provider_id: "ffmpeg_render", config: { crf: 20, preset: "medium", subtitle_mode: "soft" } },
};

export default function SettingsPage() {
  const [configs, setConfigs] = useState<ProviderConfig[]>([]);
  const [message, setMessage] = useState<string | null>(null);

  async function load() {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    const res = await fetch(`${base}/projects/00000000-0000-0000-0000-000000000000/provider-configs`);
    if (res.ok) {
      const data = (await res.json()) as ProviderConfig[];
      setConfigs(data);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function save(kind: string) {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    const fallback = defaults[kind];
    const body = {
      provider_kind: kind,
      provider_id: fallback.provider_id,
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

  return (
    <section style={{ maxWidth: 720 }}>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Provider Settings</h1>
      <p style={{ color: "#94a3b8" }}>Phase 3: lưu config vào API. Real workflow sẽ dùng config này cho từng project.</p>
      <div style={{ display: "grid", gap: 16, marginTop: 16 }}>
        {kinds.map((kind) => {
          const cfg = configFor(kind.key);
          return (
            <div key={kind.key} style={{ padding: 12, background: "#1e293b", borderRadius: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <strong>{kind.label}</strong>
                <button onClick={() => save(kind.key)} style={{ background: "#0ea5e9", color: "#0f172a", border: 0, padding: "6px 12px", cursor: "pointer" }}>
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