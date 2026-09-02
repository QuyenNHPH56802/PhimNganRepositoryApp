"use client";

import { useEffect, useState } from "react";
import { Button, Card, Input } from "@/components/ui";
import { theme } from "@/lib/theme";
import { loadToken } from "@/lib/auth";

type AuditItem = {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor: string;
  timestamp: string | null;
  payload: Record<string, unknown> | null;
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function AuditPage() {
  const [entity, setEntity] = useState("");
  const [action, setAction] = useState("");
  const [actor, setActor] = useState("");
  const [items, setItems] = useState<AuditItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedPayload, setSelectedPayload] = useState<Record<string, unknown> | null>(null);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      if (entity) params.set("entity", entity);
      if (action) params.set("action", action);
      if (actor) params.set("actor", actor);

      const token = loadToken();
      const res = await fetch(`${API_BASE}/admin/audit-logs?${params.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`Lỗi API ${res.status}`);
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
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>📜 Nhật ký Hoạt động Hệ thống (Audit Log)</h1>
          <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0" }}>
            Tra cứu và giám sát tất cả thao tác tạo dự án, thay đổi cấu hình, chạy workflow và kết xuất dữ liệu.
          </p>
        </div>
        <Button variant="primary" onClick={() => void load()}>🔍 Lọc nhật ký</Button>
      </header>

      <Card title="Bộ lọc Tìm kiếm Nhật ký">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr auto", gap: 10, alignItems: "flex-end" }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>Đối tượng (Entity Type)</span>
            <Input
              value={entity}
              onChange={(e) => setEntity(e.target.value)}
              placeholder="VD: project, user, asset"
            />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>Hành động (Action)</span>
            <Input
              value={action}
              onChange={(e) => setAction(e.target.value)}
              placeholder="VD: create, trigger_workflow"
            />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>ID Thực thể (Entity ID)</span>
            <Input
              value={actor}
              onChange={(e) => setActor(e.target.value)}
              placeholder="UUID thực thể"
            />
          </label>
          <Button type="button" onClick={() => void load()}>Tìm kiếm</Button>
        </div>
      </Card>

      <Card title="Danh sách Nhật ký Hoạt động" padded={false}>
        {loading ? (
          <div style={{ padding: 20, color: theme.textMuted, fontSize: 13 }}>Đang tải dữ liệu nhật ký…</div>
        ) : error ? (
          <div style={{ padding: 20, color: theme.danger, fontSize: 13 }}>Lỗi: {error}</div>
        ) : items.length === 0 ? (
          <div style={{ padding: 28, color: theme.textMuted, fontSize: 13, textAlign: "center" }}>
            Chưa có ghi nhận nhật ký nào phù hợp với bộ lọc.
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#0d172e" }}>
                {["Thời gian", "Đối tượng", "Hành động", "Actor", "ID Thực thể", "Chi tiết Payload"].map((h) => (
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
                  <td style={{ padding: "10px 12px", fontSize: 11, color: theme.textMuted, fontVariantNumeric: "tabular-nums" }}>
                    {item.timestamp ? new Date(item.timestamp).toLocaleString() : "—"}
                  </td>
                  <td style={{ padding: "10px 12px", fontSize: 13, fontWeight: 600 }}>{item.entity_type}</td>
                  <td style={{ padding: "10px 12px", fontSize: 12 }}>
                    <span style={{ background: "rgba(125,211,252,0.1)", color: theme.accent, padding: "2px 8px", borderRadius: 4, fontWeight: 600 }}>
                      {item.action}
                    </span>
                  </td>
                  <td style={{ padding: "10px 12px", fontSize: 12 }}>{item.actor}</td>
                  <td style={{ padding: "10px 12px", fontSize: 11, color: theme.textMuted }}>{item.entity_id}</td>
                  <td style={{ padding: "10px 12px" }}>
                    {item.payload ? (
                      <Button size="sm" onClick={() => setSelectedPayload(item.payload)}>
                        🔍 Xem Payload
                      </Button>
                    ) : (
                      <span style={{ fontSize: 11, color: theme.textMuted }}>Không có</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {selectedPayload && (
        <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "grid", placeItems: "center", zIndex: 100 }}>
          <div style={{ background: theme.bgPanel, border: `1px solid ${theme.border}`, borderRadius: 8, padding: 20, maxWidth: 600, width: "90%" }}>
            <h3 style={{ margin: "0 0 12px", fontSize: 16 }}>Chi tiết Payload Nhật ký</h3>
            <pre style={{ background: "#0a1426", padding: 12, borderRadius: 6, fontSize: 12, color: theme.accent, overflow: "auto", maxHeight: 300 }}>
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