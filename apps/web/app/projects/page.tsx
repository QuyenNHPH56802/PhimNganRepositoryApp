"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import { Button, Card, EmptyState, StatusDot, Badge } from "@/components/ui";
import { theme } from "@/lib/theme";
import type { Project } from "@/lib/types";

export default function ProjectsListPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  useEffect(() => {
    api
      .listProjects()
      .then(setProjects)
      .catch((e) => setError(e instanceof ApiError ? `${e.status}` : String(e)))
      .finally(() => setLoading(false));
  }, []);

  const filtered = projects.filter((p) => p.title.toLowerCase().includes(query.toLowerCase()));

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>Projects</h1>
          <p style={{ margin: "4px 0 0", color: theme.textMuted, fontSize: 13 }}>
            Tất cả project Trung → Việt của bạn.
          </p>
        </div>
        <Link href="/projects/new" style={{ textDecoration: "none" }}>
          <Button variant="primary">+ New Project</Button>
        </Link>
      </header>

      <Card padded={false}>
        <div style={{ padding: 12, borderBottom: `1px solid ${theme.border}` }}>
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Tìm theo tên project…"
            style={{
              background: theme.bgElevated,
              border: `1px solid ${theme.border}`,
              color: theme.text,
              padding: "8px 12px",
              borderRadius: 6,
              fontSize: 13,
              outline: "none",
              width: "100%",
              maxWidth: 320,
            }}
          />
        </div>
        {loading ? (
          <div style={{ padding: 24, color: theme.textMuted }}>Đang tải…</div>
        ) : error ? (
          <EmptyState title="Không kết nối được backend" description={error} />
        ) : filtered.length === 0 ? (
          <EmptyState title={query ? "Không tìm thấy" : "Chưa có project"} description="Tạo project mới để bắt đầu." />
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#0d172e" }}>
                {["Title", "Quality", "Status", "Tạo lúc", ""].map((h) => (
                  <th
                    key={h}
                    style={{
                      textAlign: "left",
                      padding: "10px 14px",
                      fontSize: 11,
                      color: theme.textMuted,
                      borderBottom: `1px solid ${theme.border}`,
                    }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <tr key={p.id} style={{ borderBottom: `1px solid ${theme.border}` }}>
                  <td style={{ padding: "10px 14px" }}>
                    <Link href={`/projects/${p.id}`} style={{ color: theme.accent, fontWeight: 600 }}>
                      {p.title}
                    </Link>
                  </td>
                  <td style={{ padding: "10px 14px" }}>
                    <Badge tone="info">{p.quality_mode}</Badge>
                  </td>
                  <td style={{ padding: "10px 14px" }}>
                    <span style={{ display: "inline-flex", alignItems: "center", fontSize: 12 }}>
                      <StatusDot status={p.status} />
                      {p.status}
                    </span>
                  </td>
                  <td style={{ padding: "10px 14px", color: theme.textMuted, fontSize: 12 }}>
                    {new Date(p.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: "10px 14px", textAlign: "right" }}>
                    <Link href={`/projects/${p.id}/workspace`}>
                      <Button size="sm" variant="primary">Workspace</Button>
                    </Link>
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
