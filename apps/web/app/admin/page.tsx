"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button, Card, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";
import { loadToken } from "@/lib/auth";

type OverviewData = {
  status: string;
  system_time: string;
  database: string;
  metrics: {
    projects: number;
    users: number;
    workflows: number;
    voice_profiles: number;
    audit_logs: number;
  };
  admin_user: {
    id: string;
    email: string;
    display_name?: string;
  };
};

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export default function AdminIndex() {
  const [data, setData] = useState<OverviewData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function fetchOverview() {
    setLoading(true);
    setError(null);
    try {
      const token = loadToken();
      const res = await fetch(`${API_BASE}/admin/overview`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const json = await res.json();
      setData(json);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    fetchOverview();
  }, []);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>📊 Tổng quan Hệ thống Quản trị</h1>
          <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0" }}>
            Theo dõi trạng thái máy chủ, số lượng dự án, người dùng và hoạt động hệ thống.
          </p>
        </div>
        <Button onClick={fetchOverview}>🔄 Tải lại dữ liệu</Button>
      </header>

      {loading ? (
        <div style={{ color: theme.textMuted, fontSize: 13, padding: 20 }}>Đang kiểm tra kết nối hệ thống…</div>
      ) : error ? (
        <Card title="Lỗi kết nối Quản trị">
          <div style={{ padding: 16, color: theme.danger }}>
            ❌ Không thể tải thông tin Admin Overview ({error}). Vui lòng kiểm tra đăng nhập tài khoản Quản trị.
          </div>
        </Card>
      ) : data ? (
        <>
          <section style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
            <MetricCard label="Tổng Dự án" value={data.metrics.projects} icon="📁" color={theme.accent} />
            <MetricCard label="Người dùng" value={data.metrics.users} icon="👥" color={theme.success} />
            <MetricCard label="Workflows đã chạy" value={data.metrics.workflows} icon="⚡" color={theme.warn} />
            <MetricCard label="Giọng đọc (Voices)" value={data.metrics.voice_profiles} icon="🎙" color="#a855f7" />
          </section>

          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 14 }}>
            <Card title="Trạng thái Môi trường máy chủ">
              <div style={{ display: "flex", flexDirection: "column", gap: 10, fontSize: 13 }}>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: `1px solid ${theme.border}` }}>
                  <span>Trạng thái API Engine</span>
                  <span style={{ color: theme.success, fontWeight: 600 }}>🟢 Active ({data.status})</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: `1px solid ${theme.border}` }}>
                  <span>Kết nối Cơ sở dữ liệu PostgreSQL</span>
                  <span style={{ color: theme.success, fontWeight: 600 }}>🟢 Ready ({data.database})</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0", borderBottom: `1px solid ${theme.border}` }}>
                  <span>Thời gian hệ thống máy chủ</span>
                  <span style={{ color: theme.textMuted }}>{new Date(data.system_time).toLocaleString()}</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", padding: "6px 0" }}>
                  <span>Tài khoản Admin hiện tại</span>
                  <span style={{ color: theme.accent, fontWeight: 600 }}>{data.admin_user.email}</span>
                </div>
              </div>
            </Card>

            <Card title="Lối tắt Quản trị nhanh">
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <Link href="/admin/audit" style={{ textDecoration: "none" }}>
                  <Button variant="ghost" style={{ width: "100%", justifyContent: "flex-start" }}>
                    📜 Xem Nhật ký hoạt động chi tiết (Audit Logs) →
                  </Button>
                </Link>
                <Link href="/admin/voice" style={{ textDecoration: "none" }}>
                  <Button variant="ghost" style={{ width: "100%", justifyContent: "flex-start" }}>
                    🎙 Quản lý danh sách Voice Profiles & Consent →
                  </Button>
                </Link>
                <Link href="/admin/dataset" style={{ textDecoration: "none" }}>
                  <Button variant="ghost" style={{ width: "100%", justifyContent: "flex-start" }}>
                    🧪 Chạy Kiểm định Benchmark (Golden Dataset) →
                  </Button>
                </Link>
                <Link href="/admin/flags" style={{ textDecoration: "none" }}>
                  <Button variant="ghost" style={{ width: "100%", justifyContent: "flex-start" }}>
                    🚩 Bật/tắt Feature Flags (runtime) →
                  </Button>
                </Link>
                <Link href="/admin/health" style={{ textDecoration: "none" }}>
                  <Button variant="ghost" style={{ width: "100%", justifyContent: "flex-start" }}>
                    🩺 System Health Dashboard (probes) →
                  </Button>
                </Link>
              </div>
            </Card>
          </div>
        </>
      ) : null}
    </div>
  );
}

function MetricCard({ label, value, icon, color }: { label: string; value: number; icon: string; color: string }) {
  return (
    <Card padded>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 11, color: theme.textMuted, textTransform: "uppercase", letterSpacing: 0.6 }}>{label}</div>
          <div style={{ fontSize: 28, fontWeight: 700, marginTop: 4 }}>{value}</div>
        </div>
        <div
          style={{
            fontSize: 24,
            width: 44,
            height: 44,
            borderRadius: 8,
            background: theme.bgElevated,
            border: `1px solid ${theme.border}`,
            display: "grid",
            placeItems: "center",
          }}
        >
          {icon}
        </div>
      </div>
    </Card>
  );
}
