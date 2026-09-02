"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button, Card } from "@/components/ui";
import { theme } from "@/lib/theme";
import { loadToken } from "@/lib/auth";
import { API_BASE_URL } from "@/lib/types";

interface AuditItem {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor: string;
  payload: Record<string, unknown> | null;
  created_at: string;
}

export default function ProjectAuditPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const [items, setItems] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedPayload, setSelectedPayload] = useState<Record<string, unknown> | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const token = loadToken();
      const res = await fetch(`${API_BASE_URL}/projects/${projectId}/audit`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        cache: "no-store",
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
    void load();
  }, [projectId]);

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>📜 Nhật ký Hoạt động Dự án</h1>
          <p style={{ margin: "4px 0 0", color: theme.textMuted, fontSize: 13 }}>
            Theo dõi các thao tác trên dự án: tạo, sửa, chạy workflow và xuất dữ liệu.
          </p>
        </div>
        <Button onClick={() => void load()} disabled={loading}>
          {loading ? "⏳ Đang tải…" : "🔄 Tải lại"}
        </Button>
      </header>

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

      <Card title={`Nhật ký Hoạt động (${items.length} bản ghi)`} padded={false}>
        {loading ? (
          <div style={{ padding: 24, color: theme.textMuted, fontSize: 13 }}>�ang tải…</div>
        ) : items.length === 0 ? (
          <div style={{ padding: 28, color: theme.textMuted, fontSize: 13, textAlign: "center" }}>
            Chưa có nhật ký nào cho dự án này.
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#0d172e" }}>
                {["Thời gian", "Hành động", "Đối tượng", "Actor", "Chi tiết"].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: "left",
                      padding: "10px 14px",
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
                  <td style={{ padding: "10px 14px", fontSize: 11, color: theme.textMuted, fontVariantNumeric: "tabular-nums" }}>
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: "10px 14px", fontSize: 12 }}>
                    <span
                      style={{
                        background: "rgba(125,211,252,0.1)",
                        color: theme.accent,
                        padding: "2px 8px",
                        borderRadius: 4,
                        fontWeight: 600,
                        fontSize: 11,
                      }}
                    >
                      {item.action}
                    </span>
                  </td>
                  <td style={{ padding: "10px 14px", fontSize: 13, fontWeight: 600 }}>{item.entity_type}</td>
                  <td style={{ padding: "10px 14px", fontSize: 12, color: theme.textMuted }}>{item.actor}</td>
                  <td style={{ padding: "10px 14px" }}>
                    {item.payload ? (
                      <Button size="sm" onClick={() => setSelectedPayload(item.payload)}>
                        🔍 Xem Payload
                      </Button>
                    ) : (
                      <span style={{ fontSize: 11, color: theme.textMuted }}>—</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {selectedPayload && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.7)",
            display: "grid",
            placeItems: "center",
            zIndex: 100,
          }}
          onClick={() => setSelectedPayload(null)}
        >
          <div
            style={{
              background: theme.bgPanel,
              border: `1px solid ${theme.border}`,
              borderRadius: 8,
              padding: 20,
              maxWidth: 600,
              width: "90%",
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3 style={{ margin: "0 0 12px", fontSize: 16 }}>Chi tiết Payload</h3>
            <pre
              style={{
                background: "#0a1426",
                padding: 12,
                borderRadius: 6,
                fontSize: 12,
                color: theme.accent,
                overflow: "auto",
                maxHeight: 300,
              }}
            >
              {JSON.stringify(selectedPayload, null, 2)}
            </pre>
            <div style={{ marginTop: 16, display: "flex", justifyContent: "flex-end" }}>
              <Button onClick={() => setSelectedPayload(null)}>Đóng</Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
