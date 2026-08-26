"use client";

import { useCallback, useState } from "react";

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
    <div className="space-y-3">
      <input type="file" accept="audio/*" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} />
        Tôi đã có sự đồng ý của speaker (evidence được lưu tại consent_evidence_key khi grant).
      </label>
      <button onClick={upload} disabled={!file || !consent || status === "uploading"} className="bg-blue-600 text-white px-3 py-1 rounded disabled:bg-gray-400">
        Upload
      </button>
      {progress > 0 && progress < 100 && <p>Tiến độ: {progress}%</p>}
      {error && <p className="text-red-500 text-sm">{error}</p>}
      {status === "done" && <p className="text-green-600 text-sm">Upload xong. Profile tạo ở trạng thái pending.</p>}
    </div>
  );
}