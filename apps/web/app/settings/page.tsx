"use client";

import { useEffect, useState } from "react";
import { api, ApiError } from "@/lib/api";
import { Badge, Button, Card, Input, Select } from "@/components/ui";
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

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function SettingsPage() {
  const [configs, setConfigs] = useState<ProviderConfig[]>([]);
  const [models, setModels] = useState<ModelItem[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [projectId, setProjectId] = useState<string | null>(null);
  const [installingId, setInstallingId] = useState<string | null>(null);

  // Form states for Translation LLM
  const [translateProvider, setTranslateProvider] = useState("openai_compatible_http");
  const [translateApiKey, setTranslateApiKey] = useState("");
  const [translateBaseUrl, setTranslateBaseUrl] = useState("https://api.openai.com/v1");
  const [translateModelId, setTranslateModelId] = useState("gpt-4o-mini");
  const [translateTemp, setTranslateTemp] = useState("0.2");
  const [showApiKey, setShowApiKey] = useState(false);

  // Form states for TTS
  const [ttsProvider, setTtsProvider] = useState("edge_tts");
  const [ttsApiKey, setTtsApiKey] = useState("");
  const [ttsVoiceId, setTtsVoiceId] = useState("vi-VN-HoaiMyNeural");
  const [ttsSpeed, setTtsSpeed] = useState("1.0");

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
      // ignore
    }
  }

  async function loadConfigs() {
    if (!projectId) return;
    try {
      const data = await api.listProviderConfigs(projectId);
      setConfigs(data);

      const activeTranslate = data.find((c) => c.provider_kind === "translate" && c.is_active);
      if (activeTranslate) {
        setTranslateProvider(activeTranslate.provider_id);
        const cfg = activeTranslate.config || {};
        if (cfg.api_key) setTranslateApiKey(String(cfg.api_key));
        if (cfg.base_url) setTranslateBaseUrl(String(cfg.base_url));
        if (cfg.model_id) setTranslateModelId(String(cfg.model_id));
        if (cfg.temperature) setTranslateTemp(String(cfg.temperature));
      }

      const activeTts = data.find((c) => c.provider_kind === "tts" && c.is_active);
      if (activeTts) {
        setTtsProvider(activeTts.provider_id);
        const cfg = activeTts.config || {};
        if (cfg.api_key) setTtsApiKey(String(cfg.api_key));
        if (cfg.voice_id) setTtsVoiceId(String(cfg.voice_id));
        if (cfg.speed) setTtsSpeed(String(cfg.speed));
      }
    } catch (exc) {
      if (exc instanceof ApiError) {
        setMessage(`Lỗi tải provider config: ${exc.status}`);
      }
    }
  }

  useEffect(() => {
    void loadModels();
    const interval = setInterval(loadModels, 2500);
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

  async function saveTranslateConfig(e: React.FormEvent) {
    e.preventDefault();
    if (!projectId) {
      setMessage("⚠️ Vui lòng tạo dự án trước khi lưu cấu hình Provider.");
      return;
    }
    const body = {
      provider_kind: "translate",
      provider_id: translateProvider,
      config: {
        api_key: translateApiKey.trim() || undefined,
        base_url: translateBaseUrl.trim() || undefined,
        model_id: translateModelId.trim() || "gpt-4o-mini",
        temperature: parseFloat(translateTemp) || 0.2,
      },
      is_active: true,
    };
    try {
      await api.upsertProviderConfig(projectId, body);
      setMessage("✅ Đã lưu cấu hình Dịch thuật LLM & API Key thành công!");
      await loadConfigs();
    } catch (exc) {
      setMessage(exc instanceof ApiError ? `❌ Lỗi: ${exc.status}` : String(exc));
    }
  }

  async function saveTtsConfig(e: React.FormEvent) {
    e.preventDefault();
    if (!projectId) {
      setMessage("⚠️ Vui lòng tạo dự án trước khi lưu cấu hình Provider.");
      return;
    }
    const body = {
      provider_kind: "tts",
      provider_id: ttsProvider,
      config: {
        api_key: ttsApiKey.trim() || undefined,
        voice_id: ttsVoiceId.trim() || "vi-VN-HoaiMyNeural",
        speed: parseFloat(ttsSpeed) || 1.0,
      },
      is_active: true,
    };
    try {
      await api.upsertProviderConfig(projectId, body);
      setMessage("✅ Đã lưu cấu hình Tổng hợp Giọng nói (TTS) thành công!");
      await loadConfigs();
    } catch (exc) {
      setMessage(exc instanceof ApiError ? `❌ Lỗi: ${exc.status}` : String(exc));
    }
  }

  function applyPreset(preset: "openai" | "deepseek" | "ollama") {
    if (preset === "openai") {
      setTranslateProvider("openai_compatible_http");
      setTranslateBaseUrl("https://api.openai.com/v1");
      setTranslateModelId("gpt-4o-mini");
    } else if (preset === "deepseek") {
      setTranslateProvider("openai_compatible_http");
      setTranslateBaseUrl("https://api.deepseek.com/v1");
      setTranslateModelId("deepseek-chat");
    } else if (preset === "ollama") {
      setTranslateProvider("openai_compatible_http");
      setTranslateBaseUrl("http://localhost:11434/v1");
      setTranslateModelId("qwen2.5:7b");
      setTranslateApiKey(""); // Ollama local requires no API key
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 840, display: "flex", flexDirection: "column", gap: 20 }}>
      <header>
        <h1 style={{ margin: 0, fontSize: 22 }}>⚙️ Cài Đặt Cấu Hình API Key & Mô Hình AI</h1>
        <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0" }}>
          Nhập API Key (OpenAI, DeepSeek, Azure, ElevenLabs) hoặc cấu hình Ollama local & mô hình tự host.
        </p>
      </header>

      {/* SECTION 1: LLM TRANSLATION CONFIGURATION WITH API KEY */}
      <Card title="🔑 Cấu Hình Dịch Thuật LLM & API Key (Translation LLM)">
        <form onSubmit={saveTranslateConfig} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4 }}>
            <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>Cấu hình nhanh (Presets):</span>
            <Button size="sm" type="button" onClick={() => applyPreset("openai")}>⚡ OpenAI (GPT-4o)</Button>
            <Button size="sm" type="button" onClick={() => applyPreset("deepseek")}>⚡ DeepSeek V3/R1</Button>
            <Button size="sm" type="button" onClick={() => applyPreset("ollama")}>💻 Ollama Local (Không cần Key)</Button>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>Provider Engine</span>
              <Select value={translateProvider} onChange={(e) => setTranslateProvider(e.target.value)}>
                <option value="openai_compatible_http">OpenAI Compatible HTTP (OpenAI / DeepSeek / Ollama)</option>
                <option value="cloud_qwen">Alibaba DashScope Qwen LLM</option>
                <option value="rule_based">Rule-Based Dictionary (Fallback Offline)</option>
              </Select>
            </label>

            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>Tên Model ID</span>
              <Input
                value={translateModelId}
                onChange={(e) => setTranslateModelId(e.target.value)}
                placeholder="VD: gpt-4o-mini, deepseek-chat, qwen2.5:7b"
                required
              />
            </label>
          </div>

          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>Base URL / Endpoint</span>
            <Input
              value={translateBaseUrl}
              onChange={(e) => setTranslateBaseUrl(e.target.value)}
              placeholder="VD: https://api.openai.com/v1 hoặc http://localhost:11434/v1"
              required
            />
          </label>

          <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>API Key (Khóa bảo mật)</span>
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                style={{ background: "none", border: "none", color: theme.accent, fontSize: 11, cursor: "pointer", padding: 0 }}
              >
                {showApiKey ? "👁️ Ẩn API Key" : "👁️ Hiện API Key"}
              </button>
            </div>
            <Input
              type={showApiKey ? "text" : "password"}
              value={translateApiKey}
              onChange={(e) => setTranslateApiKey(e.target.value)}
              placeholder={translateBaseUrl.includes("localhost") ? "Không bắt buộc đối với Ollama local" : "sk-proj-... / sk-..."}
            />
            <span style={{ fontSize: 11, color: theme.textMuted }}>
              {translateBaseUrl.includes("localhost")
                ? "🟢 Chế độ Local Ollama: Không cần API Key."
                : "🔒 API Key được mã hóa và lưu trữ an toàn trong Database của bạn."}
            </span>
          </label>

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 6 }}>
            <Button variant="primary" type="submit">💾 Lưu Cấu Hình LLM & API Key</Button>
          </div>
        </form>
      </Card>

      {/* SECTION 2: TTS CONFIGURATION */}
      <Card title="🎙️ Cấu Hình Tổng Hợp Giọng Nói (TTS Service & API Key)">
        <form onSubmit={saveTtsConfig} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>Engine TTS</span>
              <Select value={ttsProvider} onChange={(e) => setTtsProvider(e.target.value)}>
                <option value="edge_tts">Microsoft Edge TTS (Miễn phí - Không cần API Key)</option>
                <option value="qwen3_tts">Alibaba Qwen3 TTS (Local GPU Model)</option>
                <option value="dashscope_tts">Alibaba DashScope Qwen3 (Cloud API Key)</option>
                <option value="cloud_azure">Microsoft Azure Neural TTS (AZURE_TTS_KEY)</option>
                <option value="cloud_elevenlabs">ElevenLabs Voice Clone (ELEVENLABS_API_KEY)</option>
                <option value="cloud_google">Google Cloud Text-to-Speech (GOOGLE_TTS_KEY)</option>
                <option value="vietvoice_tts">VietVoice TTS (Local Vietnamese)</option>
                <option value="melotts_vi">MeloTTS VI (Local Lightweight)</option>
              </Select>
            </label>

            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>Giọng đọc mặc định (Voice ID)</span>
              <Input
                value={ttsVoiceId}
                onChange={(e) => setTtsVoiceId(e.target.value)}
                placeholder="VD: vi-VN-HoaiMyNeural hoặc vi-VN-NamMinhNeural"
                required
              />
            </label>
          </div>

          {["cloud_azure", "cloud_elevenlabs", "cloud_google", "dashscope_tts"].includes(ttsProvider) && (
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>API Key cho Cloud TTS</span>
              <Input
                type="password"
                value={ttsApiKey}
                onChange={(e) => setTtsApiKey(e.target.value)}
                placeholder="Nhập API Key của dịch vụ TTS Cloud"
                required
              />
            </label>
          )}

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 6 }}>
            <Button variant="primary" type="submit">💾 Lưu Cấu Hình TTS</Button>
          </div>
        </form>
      </Card>

      {/* SECTION 3: ONE-CLICK MODEL INSTALLER */}
      <Card title="📦 Cài Đặt Mô Hình AI Trực Tiếp (1-Click Model Installer)">
        <div style={{ fontSize: 12, color: theme.textMuted, marginBottom: 12 }}>
          Tải & cài đặt trực tiếp các mô hình AI local (Qwen3, VietVoice, MeloTTS, UVR5) về máy local.
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

      {message && (
        <div style={{ color: theme.success, background: "#052e16", border: "1px solid #14532d", padding: 12, borderRadius: 6, fontSize: 13 }}>
          {message}
        </div>
      )}
    </div>
  );
}
