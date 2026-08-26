"use client";

import { useState } from "react";

type QualityMode = "fast" | "balanced" | "high";

export default function NewProjectPage() {
  const [title, setTitle] = useState("");
  const [qualityMode, setQualityMode] = useState<QualityMode>("balanced");
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    try {
      const res = await fetch(`${base}/projects`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, quality_mode: qualityMode, language_profile: "zh-vi" }),
      });
      if (!res.ok) {
        setMessage(`Lỗi ${res.status}`);
        return;
      }
      const project = await res.json();
      setMessage(`Đã tạo project ${project.id}`);
    } catch (err) {
      setMessage("Không kết nối được API. Chạy docker compose trước.");
    }
  }

  return (
    <section style={{ maxWidth: 480 }}>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>New Project</h1>
      <form onSubmit={submit} style={{ display: "grid", gap: 12 }}>
        <label style={{ display: "grid", gap: 4 }}>
          <span>Tiêu đề</span>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
            style={{ padding: 8, background: "#1e293b", color: "#e2e8f0", border: "1px solid #334155" }}
          />
        </label>
        <label style={{ display: "grid", gap: 4 }}>
          <span>Quality mode</span>
          <select
            value={qualityMode}
            onChange={(e) => setQualityMode(e.target.value as QualityMode)}
            style={{ padding: 8, background: "#1e293b", color: "#e2e8f0", border: "1px solid #334155" }}
          >
            <option value="fast">Fast</option>
            <option value="balanced">Balanced</option>
            <option value="high">High</option>
          </select>
        </label>
        <button type="submit" style={{ padding: 10, background: "#0ea5e9", color: "#0f172a", border: 0, cursor: "pointer" }}>
          Tạo project
        </button>
        {message && <p style={{ color: "#7dd3fc" }}>{message}</p>}
      </form>
    </section>
  );
}