"use client";

import { useCallback, useState } from "react";
import { theme } from "@/lib/theme";

const CHUNK_SIZE = 5 * 1024 * 1024;

type ReferenceUploadProps = {
  projectId: string;
  speakerId: string;
};

export function ReferenceUpload({ projectId, speakerId }: ReferenceUploadProps) {
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "creating" | "done">("idle");

  const upload = useCallback(async () => {
    if (!file || !consent) {
      setError("Chọn file và tick consent checkbox trước.");
      return;
    }
    setError(null);
    setStatus("uploading");
    const initResponse = await fetch("/api/uploads/init", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename: file.name, mime: file.type, size: file.size, project_id: projectId }),
    });
    if (!initResponse.ok) {
      setError(`init: ${initResponse.status}`);
      setStatus("idle");
      return;
    }
    const init = await initResponse.json();
    let uploaded = 0;
    let partNumber = 1;
    while (uploaded < file.size) {
      const chunk = file.slice(uploaded, Math.min(uploaded + CHUNK_SIZE, file.size));
      const partResponse = await fetch(`/api/uploads/${init.upload_id}/parts/${partNumber}`, {
        method: "PUT",
        body: chunk,
      });
      if (!partResponse.ok) {
        setError(`part ${partNumber}: ${partResponse.status}`);
        setStatus("idle");
        return;
      }
      uploaded += chunk.size;
      setProgress(Math.round((uploaded / file.size) * 100));
      partNumber += 1;
    }
    const complete = await fetch(`/api/uploads/${init.upload_id}/complete`, { method: "POST" });
    if (!complete.ok) {
      setError(`complete: ${complete.status}`);
      setStatus("idle");
      return;
    }
    setStatus("creating");
    const create = await fetch("/api/admin/voice-profiles", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        project_id: projectId,
        speaker_id: speakerId,
        reference_audio_key: init.storage_key,
        consent_status: "pending",
      }),
    });
    if (!create.ok) {
      setError(`create: ${create.status} ${await create.text()}`);
      setStatus("idle");
      return;
    }
    setStatus("done");
  }, [file, consent, projectId, speakerId]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <input
        type="file"
        accept="audio/*"
        onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        style={{
          background: theme.bgElevated,
          border: `1px solid ${theme.border}`,
          color: theme.text,
          padding: "6px 10px",
          borderRadius: 6,
          fontSize: 13,
        }}
      />
      <label
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          fontSize: 13,
          color: theme.text,
        }}
      >
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        Tôi đã có sự đồng ý của speaker (evidence được lưu tại consent_evidence_key khi grant).
      </label>
      <button
        onClick={upload}
        disabled={!file || !consent || status === "uploading"}
        style={{
          background: theme.accentStrong,
          color: "#0b1220",
          border: "none",
          padding: "6px 14px",
          borderRadius: 6,
          fontWeight: 600,
          fontSize: 13,
          cursor: !file || !consent || status === "uploading" ? "not-allowed" : "pointer",
          opacity: !file || !consent || status === "uploading" ? 0.5 : 1,
          alignSelf: "flex-start",
        }}
      >
        Upload
      </button>
      {progress > 0 && progress < 100 && (
        <p style={{ fontSize: 13, color: theme.textMuted, margin: 0 }}>
          Tiến độ: {progress}%
        </p>
      )}
      {error && (
        <p style={{ color: theme.danger, fontSize: 13, margin: 0 }} role="alert">
          {error}
        </p>
      )}
      {status === "done" && (
        <p style={{ color: theme.success, fontSize: 13, margin: 0 }}>
          Upload xong. Profile tạo ở trạng thái pending.
        </p>
      )}
    </div>
  );
}