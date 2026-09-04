"use client";

import { useEffect, useState } from "react";
import { Button, Card, Input, Select, Textarea } from "@/components/ui";
import { theme } from "@/lib/theme";
import { loadToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";

type Sentence = {
  id: string;
  zh: string;
  vi: string;
  domain: string;
  license: string;
  provenance?: { contributor?: string };
  audio_key?: string | null;
  speaker_gender?: string;
  tags?: string[];
};

const LICENSE_OPTIONS = ["CC-BY-SA-4.0", "CC-BY-4.0", "CC0"] as const;
const DOMAIN_OPTIONS = ["vlog", "drama", "news", "review", "narration"] as const;
const API_BASE = API_BASE_URL;

export default function DatasetAdminPage() {
  const [items, setItems] = useState<Sentence[]>([]);
  const [loading, setLoading] = useState(true);
  const [zh, setZh] = useState("");
  const [vi, setVi] = useState("");
  const [domain, setDomain] = useState<(typeof DOMAIN_OPTIONS)[number]>("vlog");
  const [license, setLicense] = useState<(typeof LICENSE_OPTIONS)[number]>("CC-BY-SA-4.0");
  const [contributor, setContributor] = useState("admin@translator.local");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function loadSentences() {
    setLoading(true);
    setError(null);
    try {
      const token = loadToken();
      const res = await fetch(`${API_BASE}/admin/datasets`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const body = await res.json();
      setItems(body.items ?? []);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void loadSentences();
  }, []);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!zh.trim() || !vi.trim()) return;

    setSubmitting(true);
    setError(null);
    setMessage(null);

    try {
      const token = loadToken();
      const res = await fetch(`${API_BASE}/admin/datasets/sentences`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          id: `golden-${Date.now().toString().slice(-6)}`,
          zh: zh.trim(),
          vi: vi.trim(),
          domain,
          license,
          speaker_gender: "x",
          tags: [],
          provenance_contributor: contributor,
        }),
      });

      if (!res.ok) {
        const detail = await res.json().catch(() => ({}));
        throw new Error(detail.detail ?? `HTTP ${res.status}`);
      }

      setMessage("✅ Đã thêm cặp câu mẫu vào Golden Benchmark Dataset!");
      setZh("");
      setVi("");
      await loadSentences();
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>🧪 Tập Dữ Liệu Kiểm Định Benchmark (Golden Dataset)</h1>
          <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0" }}>
            Quản lý và đánh giá cặp câu chuẩn tiếng Trung → Việt làm căn cứ đo lường chất lượng Dịch & ASR.
          </p>
        </div>
        <Button onClick={() => void loadSentences()} disabled={loading}>
          {loading ? "⏳ Đang tải…" : "🔄 Tải lại"}
        </Button>
      </header>

      {message && (
        <div
          style={{
            background: "#052e16",
            color: theme.success,
            padding: 12,
            borderRadius: 6,
            fontSize: 12,
            border: "1px solid #14532d",
          }}
        >
          {message}
        </div>
      )}

      {error && (
        <div
          style={{
            background: "#450a0a",
            color: theme.danger,
            padding: 12,
            borderRadius: 6,
            fontSize: 12,
            border: "1px solid #7f1d1d",
          }}
        >
          ❌ Lỗi: {error}
        </div>
      )}

      <Card title="Thêm Cặp Câu Mẫu Chuẩn (Benchmark Pair)">
        <form onSubmit={submit} style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>Câu tiếng Trung chuẩn (ZH Source)</span>
              <Textarea
                value={zh}
                onChange={(e) => setZh(e.target.value)}
                placeholder="VD: 大家好，欢迎收看"
                rows={3}
                required
              />
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <span style={{ fontSize: 12, color: theme.textMuted, fontWeight: 600 }}>Bản dịch tiếng Việt chuẩn (VI Reference)</span>
              <Textarea
                value={vi}
                onChange={(e) => setVi(e.target.value)}
                placeholder="VD: Xin chào mọi người, chào mừng các bạn theo dõi"
                rows={3}
                required
              />
            </label>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>Thể loại (Domain)</span>
              <Select value={domain} onChange={(e) => setDomain(e.target.value as typeof domain)}>
                {DOMAIN_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </Select>
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>Bản quyền (License)</span>
              <Select value={license} onChange={(e) => setLicense(e.target.value as typeof license)}>
                {LICENSE_OPTIONS.map((opt) => (
                  <option key={opt} value={opt}>{opt}</option>
                ))}
              </Select>
            </label>
            <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>Người đóng góp (Contributor)</span>
              <Input value={contributor} onChange={(e) => setContributor(e.target.value)} />
            </label>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 4 }}>
            <Button variant="primary" type="submit" disabled={submitting || !zh || !vi}>
              {submitting ? "⏳ Đang thêm…" : "➕ Thêm vào Tập Dữ Liệu Benchmark"}
            </Button>
          </div>
        </form>
      </Card>

      <Card title={`Danh sách Cặp câu Mẫu (${items.length} bản ghi)`} padded={false}>
        {loading ? (
          <div style={{ padding: 24, color: theme.textMuted, fontSize: 13 }}>Đang tải…</div>
        ) : items.length === 0 ? (
          <div style={{ padding: 28, color: theme.textMuted, fontSize: 13, textAlign: "center" }}>
            Chưa có cặp câu benchmark nào. Thêm bằng form phía trên.
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#0d172e" }}>
                {["ID", "Tiếng Trung (ZH)", "Bản dịch Tiếng Việt (VI)", "Thể loại", "Bản quyền", "Người đóng góp"].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: "left",
                      padding: "10px 12px",
                      fontSize: 11,
                      fontWeight: 600,
                      color: theme.textMuted,
                      textTransform: "uppercase",
                      letterSpacing: 0.5,
                      borderBottom: `1px solid ${theme.border}`,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.id} style={{ borderBottom: `1px solid ${theme.border}` }}>
                  <td style={{ padding: "10px 12px", fontSize: 11, color: theme.textMuted, fontFamily: "monospace" }}>{item.id}</td>
                  <td style={{ padding: "10px 12px", fontSize: 13, maxWidth: 280 }}>{item.zh}</td>
                  <td style={{ padding: "10px 12px", fontSize: 13, color: theme.accent, maxWidth: 280 }}>{item.vi}</td>
                  <td style={{ padding: "10px 12px", fontSize: 12 }}>{item.domain}</td>
                  <td style={{ padding: "10px 12px", fontSize: 11, color: theme.textMuted }}>{item.license}</td>
                  <td style={{ padding: "10px 12px", fontSize: 11, color: theme.textMuted }}>
                    {item.provenance?.contributor ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>
    </div>
  );
}
