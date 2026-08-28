"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { Button, Card, EmptyState, StatusDot, Input, Select } from "@/components/ui";
import { theme } from "@/lib/theme";

export default function NewProjectPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("zh");
  const [target, setTarget] = useState("vi");
  const [mode, setMode] = useState<"fast" | "balanced" | "high">("balanced");
  const [file, setFile] = useState<File | null>(null);
  const [stage, setStage] = useState<"form" | "uploading" | "creating" | "done">("form");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!title.trim()) {
      setError("Vui lòng nhập tên project");
      return;
    }
    try {
      setStage("creating");
      const project = await api.createProject({
        title: title.trim(),
        source_language: source,
        target_language: target,
        quality_mode: mode,
        language_profile: `${source}-${target}`,
      });

      if (file) {
        setStage("uploading");
        const presign = await api.presignAsset(project.id, {
          filename: file.name,
          mime: file.type || "video/mp4",
          size: file.size,
        });
        await uploadWithProgress(presign.url, file, setProgress);
      }

      setStage("done");
      router.push(`/projects/${project.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${JSON.stringify(err.detail)}` : String(err));
      setStage("form");
    }
  }

  return (
    <div style={{ padding: 24, maxWidth: 720, margin: "0 auto", width: "100%" }}>
      <header style={{ marginBottom: 18 }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>Tạo project mới</h1>
        <p style={{ margin: "4px 0 0", color: theme.textMuted, fontSize: 13 }}>
          Upload video Trung và bắt đầu quy trình dịch + lồng tiếng Việt.
        </p>
      </header>

      <Card title="Thông tin project">
        <form onSubmit={onSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Field label="Tên project">
            <Input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="VD: Tập 1 — Phim Trung Quốc"
            />
          </Field>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <Field label="Ngôn ngữ nguồn">
              <Select value={source} onChange={(e) => setSource(e.target.value)}>
                <option value="zh">Tiếng Trung (zh)</option>
              </Select>
            </Field>
            <Field label="Ngôn ngữ đích">
              <Select value={target} onChange={(e) => setTarget(e.target.value)}>
                <option value="vi">Tiếng Việt (vi)</option>
              </Select>
            </Field>
          </div>
          <Field label="Chất lượng xử lý">
            <Select value={mode} onChange={(e) => setMode(e.target.value as "fast" | "balanced" | "high")}>
              <option value="fast">Fast — ASR nhanh, không diarization</option>
              <option value="balanced">Balanced — WhisperX + diarization</option>
              <option value="high">High — WhisperX + diarization + voice clone</option>
            </Select>
          </Field>

          <Field label="Video đầu vào (tùy chọn)">
            <label
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                justifyContent: "center",
                padding: "28px 16px",
                border: `2px dashed ${file ? theme.accent : theme.border}`,
                borderRadius: 8,
                color: file ? theme.text : theme.textMuted,
                cursor: "pointer",
                background: theme.bgElevated,
                textAlign: "center",
                transition: "border-color 120ms ease",
              }}
            >
              <input
                type="file"
                accept="video/*"
                onChange={(e) => setFile(e.target.files?.[0] ?? null)}
                style={{ display: "none" }}
              />
              <div style={{ fontSize: 22, marginBottom: 6 }}>⤴</div>
              <div style={{ fontWeight: 600 }}>
                {file ? file.name : "Kéo thả hoặc click để chọn video"}
              </div>
              <div style={{ fontSize: 12, marginTop: 4 }}>
                {file ? `${(file.size / 1024 / 1024).toFixed(1)} MB` : "MP4, MKV, MOV — tối đa 10 GB"}
              </div>
            </label>
          </Field>

          {error && (
            <div
              style={{
                background: "#450a0a",
                color: theme.danger,
                padding: "10px 12px",
                borderRadius: 6,
                fontSize: 12,
                border: "1px solid #7f1d1d",
              }}
            >
              {error}
            </div>
          )}

          {stage !== "form" && (
            <div>
              <div style={{ fontSize: 12, color: theme.textMuted, marginBottom: 4 }}>
                {stage === "creating"
                  ? "Đang tạo project…"
                  : stage === "uploading"
                    ? `Đang upload ${progress.toFixed(0)}%`
                    : "Hoàn tất — đang chuyển…"}
              </div>
              <div
                style={{
                  height: 6,
                  background: theme.bgElevated,
                  borderRadius: 3,
                  overflow: "hidden",
                }}
              >
                <div
                  style={{
                    width: `${stage === "uploading" ? progress : stage === "creating" ? 10 : 100}%`,
                    height: "100%",
                    background: theme.accent,
                    transition: "width 200ms ease",
                  }}
                />
              </div>
            </div>
          )}

          <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 6 }}>
            <Link href="/">
              <Button type="button">Huỷ</Button>
            </Link>
            <Button variant="primary" disabled={stage !== "form"} type="submit">
              Tạo project
            </Button>
          </div>
        </form>
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>{label}</span>
      {children}
    </label>
  );
}

function uploadWithProgress(url: string, file: File, onProgress: (n: number) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("PUT", url);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgress((e.loaded / e.total) * 100);
    };
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error(`upload ${xhr.status}`)));
    xhr.onerror = () => reject(new Error("upload failed"));
    xhr.send(file);
  });
}
