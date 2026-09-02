"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { Button, Card, Input, Select, ProgressBar } from "@/components/ui";
import { theme } from "@/lib/theme";
import { loadToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";

type Stage = "form" | "creating" | "uploading" | "triggering" | "done";

export default function NewProjectPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [source, setSource] = useState("zh");
  const [target, setTarget] = useState("vi");
  const [mode, setMode] = useState<"fast" | "balanced" | "high">("balanced");
  const [file, setFile] = useState<File | null>(null);
  const [stage, setStage] = useState<Stage>("form");
  const [progress, setProgress] = useState(0);
  const [stageMessage, setStageMessage] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!title.trim()) {
      setError("Vui lòng nhập tên project");
      return;
    }
    let projectId: string | null = null;
    try {
      // Stage 1: create project
      setStage("creating");
      setProgress(5);
      setStageMessage("Đang tạo project…");
      const project = await api.createProject({
        title: title.trim(),
        source_language: source,
        target_language: target,
        quality_mode: mode,
        language_profile: `${source}-${target}`,
      });
      projectId = project.id;

      // Stage 2: upload video (if provided)
      if (file) {
        setStage("uploading");
        setStageMessage("Đang upload video lên server…");
        await uploadWithProgress(project.id, file, (pct) => {
          setProgress(Math.max(10, Math.min(85, 10 + Math.round(pct * 0.75))));
        });
      } else {
        setProgress(85);
      }

      // Stage 3: trigger workflow pipeline
      setStage("triggering");
      setProgress(92);
      setStageMessage("Đang khởi động pipeline xử lý…");
      try {
        await api.triggerWorkflow(project.id, { quality_mode: mode });
      } catch (wfErr) {
        // Backend may not be available; still allow user to enter workspace
        console.warn("triggerWorkflow failed:", wfErr);
      }

      setStage("done");
      setProgress(100);
      setStageMessage("Hoàn tất — đang chuyển sang workspace…");
      setTimeout(() => {
        router.push(`/projects/${project.id}/workspace`);
      }, 900);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? `${err.status}: ${JSON.stringify(err.detail)}`
          : String(err),
      );
      setStage("form");
    }
  }

  const stageLabel: Record<Stage, string> = {
    form: "",
    creating: "Đang tạo project…",
    uploading: file ? `Đang upload (${progress.toFixed(0)}%)` : "Đang chuẩn bị…",
    triggering: "Đang khởi động pipeline xử lý…",
    done: "Hoàn tất — đang chuyển…",
  };

  const showProgress = stage !== "form";

  return (
    <div style={{ padding: 24, maxWidth: 720, margin: "0 auto", width: "100%" }}>
      <header style={{ marginBottom: 18 }}>
        <h1 style={{ margin: 0, fontSize: 22 }}>Tạo project mới</h1>
        <p style={{ margin: "4px 0 0", color: theme.textMuted, fontSize: 13 }}>
          Upload video Trung, hệ thống sẽ xử lý ngay tại đây và đưa vào workspace.
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
            <Select
              value={mode}
              onChange={(e) => setMode(e.target.value as "fast" | "balanced" | "high")}
            >
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

          {showProgress && (
            <ProgressBar value={progress} hint={stageLabel[stage]} />
          )}

          <div style={{ display: "flex", gap: 10, justifyContent: "flex-end", marginTop: 6 }}>
            <Link href="/">
              <Button type="button" disabled={stage !== "form"}>
                Huỷ
              </Button>
            </Link>
            <Button variant="primary" disabled={stage !== "form"} type="submit">
              {stage === "form" ? "Tạo project & xử lý" : "Đang xử lý…"}
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

async function uploadWithProgress(
  projectId: string,
  file: File,
  onProgress: (n: number) => void,
): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    const formData = new FormData();
    formData.append("file", file);

    const xhr = new XMLHttpRequest();
    xhr.upload.addEventListener("progress", (e) => {
      if (e.lengthComputable) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    });
    xhr.addEventListener("load", () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        onProgress(100);
        resolve();
      } else {
        reject(new Error(`Upload failed: HTTP ${xhr.status}`));
      }
    });
    xhr.addEventListener("error", () => reject(new Error("Network error during upload")));
    xhr.addEventListener("abort", () => reject(new Error("Upload aborted")));

    const token = loadToken();
    xhr.open("POST", `${API_BASE_URL}/projects/${projectId}/assets:upload`);
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.send(formData);
  });
}
