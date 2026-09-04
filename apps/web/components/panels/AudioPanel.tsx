"use client";

import { useEffect, useState } from "react";
import { Button, Card } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useEditor } from "@/lib/store";
import { api } from "@/lib/api";
import { useToast } from "@/lib/toast";
import { humanizeError } from "@/lib/errorMessage";

const tracks = [
  { id: "original", label: "Original (ZH)", color: theme.speaker1 },
  { id: "voice_vi", label: "Voice (VI)", color: theme.speaker2 },
  { id: "music", label: "Music", color: theme.speaker3 },
  { id: "sfx", label: "SFX", color: theme.speaker4 },
];

export function AudioPanel() {
  const [muted, setMuted] = useState<Record<string, boolean>>({});
  const [solo, setSolo] = useState<Record<string, boolean>>({});
  const audioMixGains = useEditor((s) => s.audioMixGains);
  const setAudioMixGain = useEditor((s) => s.setAudioMixGain);
  const setAudioMixGains = useEditor((s) => s.setAudioMixGains);
  const projectId = useEditor((s) => s.projectId);
  const [processing, setProcessing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [musicInfo, setMusicInfo] = useState<any>(null);
  const { toast } = useToast();

  // Load music info on mount
  useEffect(() => {
    if (!projectId) return;
    api.getMusicTrack(projectId).then((data) => {
      setMusicInfo(data.music);
    }).catch(() => {
      // No music uploaded yet
    });
  }, [projectId]);

  function toggleMute(id: string) {
    setMuted((prev) => ({ ...prev, [id]: !prev[id] }));
  }

  function toggleSolo(id: string) {
    setSolo((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      // If any track is soloed, all non-soloed tracks are effectively muted.
      const anySolo = Object.values(next).some(Boolean);
      if (anySolo) {
        const mutedFromSolo: Record<string, boolean> = {};
        for (const t of tracks) mutedFromSolo[t.id] = !next[t.id];
        setMuted((prevMuted) => ({ ...prevMuted, ...mutedFromSolo }));
      } else {
        // Turning off the last solo clears the implicit mutes.
        setMuted({});
      }
      return next;
    });
  }

  function formatGain(g: number): string {
    if (g === 0) return "-∞";
    const db = 20 * Math.log10(g);
    return `${db >= 0 ? "+" : ""}${db.toFixed(1)} dB`;
  }

  async function handleAutoMix() {
    if (!projectId) {
      toast("Vui lòng chọn project trước", "warn");
      return;
    }
    setProcessing(true);
    try {
      const result = await api.autoMixAudio(projectId, audioMixGains);
      if (result?.gains) {
        setAudioMixGains(result.gains);
        toast("Đã cân bằng mix tự động", "success");
      }
    } catch (err) {
      toast(humanizeError(err, "Cân bằng audio").title, "danger");
    } finally {
      setProcessing(false);
    }
  }

  function handleResetGains() {
    setAudioMixGains({ original: 1, voice_vi: 1, music: 0.5, sfx: 0.7 });
    setMuted({});
    setSolo({});
  }

  async function handleMusicUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file || !projectId) return;

    // Validate file type
    if (!file.type.startsWith("audio/")) {
      toast("Vui lòng chọn file audio (MP3, WAV, etc.)", "danger");
      return;
    }

    // Validate file size (50MB max)
    if (file.size > 50 * 1024 * 1024) {
      toast("File quá lớn (tối đa 50MB)", "danger");
      return;
    }

    setUploading(true);
    try {
      // Step 1: Get presign URL
      const presignData = await api.presignMusicAsset(projectId, {
        filename: file.name,
        mime: file.type,
        size: file.size,
      });

      // Step 2: Upload file to storage
      const uploadHeaders = new Headers(presignData.headers || {});
      uploadHeaders.set("Content-Type", file.type);

      const uploadResponse = await fetch(presignData.url, {
        method: "PUT",
        headers: uploadHeaders,
        body: file,
      });

      if (!uploadResponse.ok) {
        throw new Error(`Upload failed: ${uploadResponse.statusText}`);
      }

      // Step 3: Create music track
      const trackResult = await api.createMusicTrack(projectId, {
        asset_id: presignData.asset_id,
      });

      setMusicInfo({
        asset_id: presignData.asset_id,
        track_id: trackResult.track_id,
        storage_key: trackResult.storage_key,
        filename: file.name,
        size: file.size,
        mime: file.type,
        url: `/local-assets/${trackResult.storage_key}`,
      });

      toast("Đã upload nhạc nền thành công", "success");
    } catch (err) {
      toast(humanizeError(err, "Upload nhạc nền").title, "danger");
    } finally {
      setUploading(false);
      // Reset input
      e.target.value = "";
    }
  }

  return (
    <Card padded={false}>
      <div
        style={{
          padding: "10px 12px",
          borderBottom: `1px solid ${theme.border}`,
          display: "flex",
          alignItems: "center",
          gap: 10,
          background: "#0d172e",
        }}
      >
        <strong style={{ fontSize: 13 }}>Audio Mix</strong>
        <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
          <Button
            size="sm"
            variant="ghost"
            disabled={processing}
            onClick={handleResetGains}
          >
            ↺ Reset
          </Button>
          <Button
            size="sm"
            disabled={processing}
            onClick={handleAutoMix}
          >
            {processing ? "..." : "⚖️"} Cân bằng tự động
          </Button>
        </div>
      </div>

      {/* Music upload section */}
      <div
        style={{
          padding: "12px",
          borderBottom: `1px solid ${theme.border}`,
          background: theme.bgPanel,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
          <strong style={{ fontSize: 12 }}>🎵 Nhạc nền</strong>
          {musicInfo && (
            <span style={{ fontSize: 11, color: theme.textMuted }}>
              {musicInfo.filename}
            </span>
          )}
        </div>
        <label style={{ display: "inline-block", cursor: uploading ? "default" : "pointer" }}>
          <input
            type="file"
            accept="audio/*"
            onChange={handleMusicUpload}
            disabled={uploading}
            style={{ display: "none" }}
          />
          <Button
            size="sm"
            variant={musicInfo ? "ghost" : "default"}
            disabled={uploading}
            onClick={(e) => e.preventDefault()}
          >
            {uploading ? "⏳ Đang tải..." : musicInfo ? "📁 Thay đổi" : "📁 Upload nhạc nền"}
          </Button>
        </label>
        {musicInfo && (
          <div style={{ fontSize: 10, color: theme.textMuted, marginTop: 4 }}>
            {(musicInfo.size / 1024 / 1024).toFixed(2)} MB • {musicInfo.mime}
          </div>
        )}
      </div>
      
      {tracks.map((t) => {
        const isMuted = muted[t.id];
        const isSolo = solo[t.id];
        const gain = isMuted ? 0 : audioMixGains[t.id] ?? 1;
        
        return (
          <div
            key={t.id}
            style={{
              padding: "12px",
              borderBottom: `1px solid ${theme.border}`,
              display: "grid",
              gridTemplateColumns: "120px 80px 1fr 70px",
              gap: 12,
              alignItems: "center",
              opacity: isMuted ? 0.5 : 1,
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ width: 10, height: 10, borderRadius: 999, background: t.color }} />
              <span style={{ fontSize: 13, fontWeight: 600 }}>{t.label}</span>
            </div>
            <div style={{ display: "flex", gap: 4 }}>
              <Button
                size="sm"
                variant={isMuted ? "primary" : "default"}
                title="Tắt tiếng"
                onClick={() => toggleMute(t.id)}
              >
                M
              </Button>
              <Button
                size="sm"
                variant={isSolo ? "primary" : "default"}
                title="Chỉ nghe kênh này"
                onClick={() => toggleSolo(t.id)}
              >
                S
              </Button>
            </div>
            <input
              type="range"
              min={0}
              max={1.5}
              step={0.01}
              value={gain}
              onChange={(e) => setAudioMixGain(t.id, parseFloat(e.target.value))}
              style={{ width: "100%" }}
              disabled={isMuted}
            />
            <span style={{ fontSize: 11, color: theme.textMuted, textAlign: "right" }}>
              {formatGain(gain)}
            </span>
          </div>
        );
      })}
      
      <div style={{ padding: 12, background: theme.bgPanel }}>
        <div style={{ fontSize: 11, color: theme.textMuted, marginBottom: 8 }}>
          Mẹo: Nhấn M để tắt tiếng, S để chỉ nghe kênh đó
        </div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          <Button size="sm" variant="ghost" onClick={() => setAudioMixGain("voice_vi", 1.2)}>
            Tăng voice +20%
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setAudioMixGain("music", 0.3)}>
            Giảm nhạc -50%
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setAudioMixGains({ original: 0, voice_vi: 1, music: 0, sfx: 0 })}>
            Chỉ voice VI
          </Button>
        </div>
      </div>
    </Card>
  );
}
