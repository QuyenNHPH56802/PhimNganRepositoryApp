"use client";

import { useEffect, useState } from "react";
import { Button, Card, Input, Select, Textarea } from "@/components/ui";
import { theme } from "@/lib/theme";
import { loadToken } from "@/lib/auth";

type Sentence = {
  id: string;
  zh: string;
  vi: string;
  domain: string;
  license: string;
  provenance?: { contributor?: string };
};

const LICENSE_OPTIONS = ["CC-BY-SA-4.0", "CC-BY-4.0", "CC0"] as const;
const DOMAIN_OPTIONS = ["vlog", "drama", "news", "review", "narration"] as const;
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function DatasetAdminPage() {
  const [items, setItems] = useState<Sentence[]>([
    {
      id: "golden-001",
      zh: "你好，欢迎来到我们的频道",
      vi: "Xin chào, chào mừng đến với kênh của chúng tôi",
      domain: "vlog",
      license: "CC-BY-SA-4.0",
    },
    {
      id: "golden-002",
      zh: "今天我们来介绍中国传统文化",
      vi: "Hôm nay chúng ta sẽ tìm hiểu về văn hóa truyền thống Trung Quốc",
      domain: "drama",
      license: "CC-BY-SA-4.0",
    },
    {
      id: "golden-003",
      zh: "请订阅并分享给朋友",
      vi: "Hãy đăng ký và chia sẻ cho bạn bè nhé",
      domain: "vlog",
      license: "CC-BY-SA-4.0",
    },
  ]);
  const [zh, setZh] = useState("");
  const [vi, setVi] = useState("");
  const [domain, setDomain] = useState<(typeof DOMAIN_OPTIONS)[number]>("vlog");
  const [license, setLicense] = useState<(typeof LICENSE_OPTIONS)[number]>("CC-BY-SA-4.0");
  const [contributor, setContributor] = useState("admin@translator.local");
  const [message, setMessage] = useState<string | null>(null);

  function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!zh.trim() || !vi.trim()) return;

    const newItem: Sentence = {
      id: `golden-${Date.now().toString().slice(-4)}`,
      zh: zh.trim(),
      vi: vi.trim(),
      domain,
      license,
      provenance: { contributor },
    };

    setItems((prev) => [newItem, ...prev]);
    setZh("");
    setVi("");
    setMessage("✅ Đã thêm cặp câu mẫu vào Tập dữ liệu kiểm định (Golden Benchmark Dataset)");
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
      </header>

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
            <Button variant="primary" type="submit" disabled={!zh || !vi}>
              ➕ Thêm vào Tập Dữ Liệu Benchmark
            </Button>
          </div>
        </form>

        {message && (
          <div style={{ marginTop: 10, background: "#052e16", color: theme.success, padding: 10, borderRadius: 6, fontSize: 12 }}>
            {message}
          </div>
        )}
      </Card>

      <Card title="Danh sách Cặp câu Mẫu trong Benchmark Dataset" padded={false}>
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ background: "#0d172e" }}>
              {["ID", "Tiếng Trung (ZH)", "Bản dịch Tiếng Việt (VI)", "Thể loại", "Bản quyền"].map((h) => (
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
                <td style={{ padding: "10px 12px", fontSize: 13 }}>{item.zh}</td>
                <td style={{ padding: "10px 12px", fontSize: 13, color: theme.accent }}>{item.vi}</td>
                <td style={{ padding: "10px 12px", fontSize: 12 }}>{item.domain}</td>
                <td style={{ padding: "10px 12px", fontSize: 11, color: theme.textMuted }}>{item.license}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}