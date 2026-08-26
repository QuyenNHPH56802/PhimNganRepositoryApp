"use client";

import { useState } from "react";

export default function UploadPage({ params }: { params: { id: string } }) {
  const [file, setFile] = useState<File | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  async function upload(event: React.FormEvent) {
    event.preventDefault();
    if (!file) return;
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    try {
      const presignRes = await fetch(`${base}/projects/${params.id}/assets:presign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: file.name, mime: file.type || "application/octet-stream", size: file.size }),
      });
      if (!presignRes.ok) {
        setMessage(`Lỗi presign ${presignRes.status}`);
        return;
      }
      const presign = await presignRes.json();
      const putRes = await fetch(presign.url, { method: "PUT", headers: presign.headers, body: file });
      if (!putRes.ok) {
        setMessage(`Lỗi upload ${putRes.status}`);
        return;
      }
      setMessage(`Uploaded key=${presign.key}`);
    } catch {
      setMessage("Không kết nối được API.");
    }
  }

  return (
    <section style={{ maxWidth: 480 }}>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Upload asset</h1>
      <form onSubmit={upload} style={{ display: "grid", gap: 12 }}>
        <input type="file" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
        <button type="submit" disabled={!file} style={{ padding: 10, background: "#0ea5e9", color: "#0f172a", border: 0 }}>
          Upload
        </button>
        {message && <p style={{ color: "#7dd3fc" }}>{message}</p>}
      </form>
    </section>
  );
}