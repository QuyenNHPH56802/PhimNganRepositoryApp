"use client";

import { useState, useCallback, useEffect, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { loadToken } from "@/lib/auth";
import { theme } from "@/lib/theme";
import { API_BASE_URL } from "@/lib/types";

const MAX_FILE_SIZE = 500 * 1024 * 1024; // 500MB
// Accept anything that looks like video — the validation label below lists the
// formats we test against, but MIME sniffing is permissive so MOV/WebM uploads
// from cameras and screen recorders don't get rejected on a missing type.
const ALLOWED_TYPES = ["video/mp4", "video/quicktime", "video/webm", "video/x-matroska"];

export default function UploadPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const projectId = params.id;
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState<number>(0);
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const dropRef = useRef<HTMLDivElement>(null);
  const xhrRef = useRef<XMLHttpRequest | null>(null);
  const [qualityMode, setQualityMode] = useState<"fast" | "balanced" | "high">("balanced");

  const handleFile = useCallback((f: File) => {
    // Validate file type
    if (!f.type.startsWith("video/") && !ALLOWED_TYPES.includes(f.type)) {
      setError("Vui lòng chọn file video (MP4, MOV, WebM, MKV)");
      return;
    }
    
    // Validate file size
    if (f.size > MAX_FILE_SIZE) {
      setError(`File quá lớn. Kích thước tối đa là ${MAX_FILE_SIZE / (1024 * 1024)}MB`);
      return;
    }
    
    setFile(f);
    setError(null);
    setStatus(null);
    setProgress(0);
  }, []);

  const handleUpload = useCallback(async () => {
    if (!file || !projectId) return;
    
    setUploading(true);
    setError(null);
    setStatus("Đang chuẩn bị tải lên...");
    setProgress(0);

    const formData = new FormData();
    formData.append("file", file);

    try {
      // Use XHR for progress tracking
      const token = loadToken();
      
      const xhr = new XMLHttpRequest();
      xhrRef.current = xhr;
      
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const pct = Math.round((e.loaded / e.total) * 100);
          setProgress(pct);
          setStatus(`Đang tải lên: ${pct}%`);
        }
      });
      
      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const result = JSON.parse(xhr.responseText);
            setProgress(100);
            setStatus("✅ Tải lên thành công! Đang khởi động pipeline xử lý...");

            // Auto-trigger workflow after upload
            setTimeout(async () => {
              try {
                await api.triggerWorkflow(projectId, { quality_mode: qualityMode });
                setStatus("🚀 Pipeline đã khởi động! Chuyển sang workspace...");
                setTimeout(() => {
                  router.push(`/projects/${projectId}/workspace`);
                }, 1500);
              } catch (wfErr) {
                setError("Tải lên thành công nhưng không khởi động được pipeline: " + (wfErr instanceof Error ? wfErr.message : String(wfErr)));
                setUploading(false);
              }
            }, 500);
          } catch {
            setError("Phản hồi từ server không hợp lệ");
            setUploading(false);
          }
        } else {
          let errorMsg = `Lỗi ${xhr.status}: ${xhr.statusText}`;
          try {
            const errData = JSON.parse(xhr.responseText);
            if (errData.detail) errorMsg = errData.detail;
          } catch {}
          setError(errorMsg);
          setUploading(false);
        }
      });
      
      xhr.addEventListener("error", () => {
        setError("Lỗi mạng. Vui lòng thử lại.");
        setUploading(false);
      });
      
      xhr.addEventListener("abort", () => {
        setStatus("Đã hủy tải lên");
        setUploading(false);
      });

      xhr.open("POST", `${API_BASE_URL}/projects/${projectId}/assets:upload`);
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      }
      xhr.send(formData);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi không xác định");
      setUploading(false);
    }
  }, [file, projectId, router]);

  function cancelUpload() {
    if (xhrRef.current) {
      xhrRef.current.abort();
    }
    setUploading(false);
    setProgress(0);
    setStatus("Đã hủy");
  }

  useEffect(() => {
    function onDragover(e: DragEvent) {
      e.preventDefault();
      setIsDragging(true);
    }
    function onDragleave(e: DragEvent) {
      if (!dropRef.current?.contains(e.relatedTarget as Node)) {
        setIsDragging(false);
      }
    }
    function onDrop(e: DragEvent) {
      e.preventDefault();
      setIsDragging(false);
      const f = e.dataTransfer?.files[0];
      if (f) handleFile(f);
    }
    window.addEventListener("dragover", onDragover);
    window.addEventListener("dragleave", onDragleave);
    window.addEventListener("drop", onDrop);
    return () => {
      window.removeEventListener("dragover", onDragover);
      window.removeEventListener("dragleave", onDragleave);
      window.removeEventListener("drop", onDrop);
    };
  }, [handleFile]);

  return (
    <div
      style={{
        maxWidth: 600,
        margin: "40px auto",
        padding: 24,
        background: theme.bgElevated,
        borderRadius: 12,
        border: `1px solid ${theme.border}`,
      }}
    >
      <h1 style={{ fontSize: 22, marginBottom: 8, color: theme.text }}>
        📤 Tải lên Video
      </h1>
      <p style={{ fontSize: 13, color: theme.textMuted, marginBottom: 24 }}>
        Chọn file video để bắt đầu quy trình dịch. Hỗ trợ MP4, MOV, WebM, MKV. Tối đa 500MB.{" "}
        <strong style={{ color: theme.text }}>Sau khi upload thành công, hệ thống sẽ tự động chạy pipeline
        và chuyển sang Không gian làm việc.</strong>
      </p>

      {/* Quality mode selector */}
      <div style={{ marginBottom: 20, display: "flex", gap: 8, flexWrap: "wrap" }}>
        {([
          ["fast", "🚀 Fast", "Chỉ phụ đề (subtitles) — nhanh nhất"],
          ["balanced", "⚡ Balanced", "Phụ đề + lồng tiếng Edge TTS — cân bằng"],
          ["high", "🎯 High", "Phụ đề + nhân bản giọng (voice cloning) — chất lượng cao nhất"],
        ] as const).map(([mode, label, desc]) => (
          <button
            key={mode}
            onClick={() => !uploading && setQualityMode(mode)}
            disabled={uploading}
            style={{
              flex: 1,
              minWidth: 160,
              padding: "10px 12px",
              border: `2px solid ${qualityMode === mode ? theme.accent : theme.border}`,
              borderRadius: 8,
              background: qualityMode === mode ? "rgba(125,211,252,0.10)" : theme.bgPanel,
              color: qualityMode === mode ? theme.accent : theme.textMuted,
              fontSize: 12,
              fontWeight: 600,
              cursor: uploading ? "not-allowed" : "pointer",
              textAlign: "left",
              opacity: uploading ? 0.5 : 1,
            }}
          >
            <div>{label}</div>
            <div style={{ fontSize: 10, fontWeight: 400, marginTop: 2, opacity: 0.8 }}>{desc}</div>
          </button>
        ))}
      </div>

      <div
        ref={dropRef}
        style={{
          border: `2px dashed ${isDragging ? theme.accent : file ? theme.accent : theme.border}`,
          borderRadius: 8,
          padding: 32,
          textAlign: "center",
          cursor: uploading ? "not-allowed" : "pointer",
          background: isDragging
            ? "rgba(125,211,252,0.08)"
            : file
            ? "rgba(125,211,252,0.05)"
            : "transparent",
          transition: "all 0.2s",
          position: "relative",
          opacity: uploading ? 0.6 : 1,
        }}
        onClick={() => !uploading && document.getElementById("file-input")?.click()}
        onDragOver={(e) => { e.preventDefault(); !uploading && setIsDragging(true); }}
        onDragLeave={() => !uploading && setIsDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          !uploading && setIsDragging(false);
          const f = e.dataTransfer?.files[0];
          if (f) handleFile(f);
        }}
      >
        {isDragging && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(125,211,252,0.1)",
              borderRadius: 6,
              fontSize: 16,
              fontWeight: 600,
              color: theme.accent,
            }}
          >
            Thả file vào đây...
          </div>
        )}
        <input
          id="file-input"
          type="file"
          accept="video/*"
          style={{ display: "none" }}
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) handleFile(f);
          }}
        />
        {file ? (
          <div>
            <div style={{ fontSize: 32, marginBottom: 8 }}>🎬</div>
            <div style={{ fontSize: 14, color: theme.text, fontWeight: 600 }}>
              {file.name}
            </div>
            <div style={{ fontSize: 12, color: theme.textMuted, marginTop: 4 }}>
              {(file.size / (1024 * 1024)).toFixed(1)} MB • {file.type}
            </div>
          </div>
        ) : (
          <div>
            <div style={{ fontSize: 32, marginBottom: 8 }}>📁</div>
            <div style={{ fontSize: 14, color: theme.textMuted }}>
              Nhấn để chọn file video hoặc kéo thả vào đây
            </div>
          </div>
        )}
      </div>

      {/* Progress bar */}
      {uploading && (
        <div style={{ marginTop: 16 }}>
          <div
            style={{
              height: 8,
              background: theme.bgPanel,
              borderRadius: 4,
              overflow: "hidden",
            }}
          >
            <div
              style={{
                height: "100%",
                width: `${progress}%`,
                background: theme.accent,
                transition: "width 200ms ease",
              }}
            />
          </div>
        </div>
      )}

      {/* Status message */}
      {status && (
        <p style={{ marginTop: 12, fontSize: 13, color: theme.textMuted }}>{status}</p>
      )}

      {/* Error message */}
      {error && (
        <div
          style={{
            marginTop: 12,
            background: "#450a0a",
            color: theme.danger,
            padding: 10,
            borderRadius: 6,
            fontSize: 12,
            border: "1px solid #7f1d1d",
          }}
        >
          ❌ {error}
        </div>
      )}

      {/* Upload/Cancel/Retry button */}
      <div style={{ display: "flex", gap: 8, marginTop: 16 }}>
        {error && !uploading ? (
          <button
            onClick={handleUpload}
            disabled={!file}
            style={{
              flex: 1,
              padding: "12px 0",
              background: !file ? theme.bgPanel : theme.danger,
              color: !file ? theme.textMuted : "#fff",
              border: "none",
              borderRadius: 6,
              fontSize: 14,
              fontWeight: 600,
              cursor: !file ? "not-allowed" : "pointer",
            }}
          >
            🔄 Thử lại
          </button>
        ) : (
          <button
            onClick={uploading ? cancelUpload : handleUpload}
            disabled={!file || (uploading === false && !!error)}
            style={{
              flex: 1,
              padding: "12px 0",
              background: !file || error ? theme.bgPanel : uploading ? theme.warn : theme.accent,
              color: !file || error ? theme.textMuted : "#0f172a",
              border: "none",
              borderRadius: 6,
              fontSize: 14,
              fontWeight: 600,
              cursor: !file || error ? "not-allowed" : "pointer",
            }}
          >
            {uploading ? "⏳ Đang tải lên..." : "🚀 Tải lên + chạy Balanced ngay"}
          </button>
        )}

        {uploading && (
          <button
            onClick={cancelUpload}
            style={{
              padding: "12px 16px",
              background: theme.bgPanel,
              color: theme.text,
              border: "none",
              borderRadius: 6,
              fontSize: 14,
              fontWeight: 600,
              cursor: "pointer",
            }}
          >
            Hủy
          </button>
        )}
      </div>

      <div style={{ marginTop: 24, fontSize: 11, color: theme.textDim }}>
        Project ID: {projectId}
      </div>
    </div>
  );
}
