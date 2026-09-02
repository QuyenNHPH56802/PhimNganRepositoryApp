"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { Button, Card, EmptyState, StatusDot, Badge } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useT } from "@/lib/i18n";
import type { Project } from "@/lib/types";

export default function DashboardPage() {
  const { t } = useT();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api
      .listProjects()
      .then((rows) => {
        if (!cancelled) setProjects(rows);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setError(err instanceof ApiError ? `${err.status} ${err.message}` : String(err));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const recent = projects.slice(0, 6);
  const processing = projects.filter((p) =>
    ["processing", "uploading", "asr_processing", "translating", "tts_processing", "rendering", "audio_mixing", "analyzing"].includes(
      p.status,
    ),
  ).length;
  const failed = projects.filter((p) => p.status === "failed").length;
  const completed = projects.filter((p) => p.status === "ready").length;

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16, minHeight: "100%" }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>{t("nav.dashboard", "Bảng điều khiển")}</h1>
          <p style={{ margin: "4px 0 0", color: theme.textMuted, fontSize: 13 }}>
            {t("dashboard.subtitle", "Quản lý project, theo dõi tiến trình xử lý video Trung → Việt.")}
          </p>
        </div>
        <Link href="/projects/new" style={{ textDecoration: "none" }}>
          <Button variant="primary">{t("dashboard.createButton", "+ Tạo project China → Việt")}</Button>
        </Link>
      </header>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
        <StatCard label={t("dashboard.total", "Tổng project")} value={projects.length} accent={theme.accent} />
        <StatCard label={t("dashboard.processing", "Đang xử lý")} value={processing} accent={theme.warn} />
        <StatCard label={t("dashboard.completed", "Hoàn thành")} value={completed} accent={theme.success} />
        <StatCard label={t("dashboard.failed", "Thất bại")} value={failed} accent={theme.danger} />
      </section>

      <Card
        title={t("dashboard.recent", "Project gần đây")}
        action={
          <Link href="/projects" style={{ color: theme.accent, fontSize: 12 }}>
            {t("dashboard.viewAll", "Xem tất cả →")}
          </Link>
        }
        padded={false}
      >
        {loading ? (
          <div style={{ padding: 24, color: theme.textMuted, fontSize: 13 }}>{t("common.loading", "Đang tải…")}</div>
        ) : error ? (
          <EmptyState
            title={t("errors.networkError", "Không kết nối được backend")}
            description={`${error}. ${t("errors.checkApiUrl", "Kiểm tra API_BASE_URL và FastAPI server.")}`}
            action={
              <Link href="/projects/new">
                <Button>{t("dashboard.manualCreate", "Tạo project thủ công")}</Button>
              </Link>
            }
          />
        ) : recent.length === 0 ? (
          <EmptyState
            title={t("dashboard.emptyTitle", "Chưa có project nào")}
            description={t("dashboard.emptyDesc", "Upload video Trung đầu tiên để bắt đầu quy trình dịch và lồng tiếng.")}
            action={
              <Link href="/projects/new">
                <Button variant="primary">{t("project.createButton", "Tạo dự án")}</Button>
              </Link>
            }
          />
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#0d172e" }}>
                {[t("dashboard.colTitle", "Tiêu đề"), t("dashboard.colQuality", "Chất lượng"), t("dashboard.colStatus", "Trạng thái"), t("dashboard.colCreated", "Tạo lúc")].map((h) => (
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
              {recent.map((p) => (
                <tr key={p.id} style={{ borderBottom: `1px solid ${theme.border}` }}>
                  <td style={{ padding: "10px 14px" }}>
                    <Link
                      href={`/projects/${p.id}`}
                      style={{ color: theme.accent, fontWeight: 600 }}
                    >
                      {p.title}
                    </Link>
                  </td>
                  <td style={{ padding: "10px 14px" }}>
                    <Badge tone="info">{t(`qualityMode.${p.quality_mode}`, p.quality_mode)}</Badge>
                  </td>
                  <td style={{ padding: "10px 14px" }}>
                    <span style={{ display: "inline-flex", alignItems: "center", fontSize: 12 }}>
                      <StatusDot status={p.status} />
                      {t(`status.${p.status}`, p.status)}
                    </span>
                  </td>
                  <td style={{ padding: "10px 14px", color: theme.textMuted, fontSize: 12 }}>
                    {new Date(p.created_at).toLocaleString()}
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

function StatCard({
  label,
  value,
  accent,
}: {
  label: string;
  value: number;
  accent: string;
}) {
  return (
    <Card padded>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 11, color: theme.textMuted, textTransform: "uppercase", letterSpacing: 0.6 }}>
            {label}
          </div>
          <div style={{ fontSize: 26, fontWeight: 700, marginTop: 4 }}>{value}</div>
        </div>
        <div
          style={{
            width: 8,
            height: 36,
            borderRadius: 4,
            background: accent,
            opacity: 0.6,
          }}
        />
      </div>
    </Card>
  );
}
