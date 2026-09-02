"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { Button, Card, EmptyState, StatusDot, Badge, Modal } from "@/components/ui";
import { theme } from "@/lib/theme";
import type { Project } from "@/lib/types";

export default function ProjectsListPage() {
  const router = useRouter();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [pendingDelete, setPendingDelete] = useState<Project | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    api
      .listProjects()
      .then(setProjects)
      .catch((e) => setError(e instanceof ApiError ? `${e.status}` : String(e)))
      .finally(() => setLoading(false));
  }, []);

  const filtered = projects.filter((p) => p.title.toLowerCase().includes(query.toLowerCase()));

  async function confirmDelete() {
    if (!pendingDelete) return;
    setDeleting(true);
    setDeleteError(null);
    try {
      await api.deleteProject(pendingDelete.id);
      setProjects((prev) => prev.filter((p) => p.id !== pendingDelete.id));
      setPendingDelete(null);
    } catch (err) {
      setDeleteError(
        err instanceof ApiError ? `${err.status}: ${JSON.stringify(err.detail)}` : String(err),
      );
    } finally {
      setDeleting(false);
    }
  }

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
          <EmptyState
            title={query ? "Không tìm thấy" : "Chưa có project"}
            description="Tạo project mới để bắt đầu."
          />
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr style={{ background: "#0d172e" }}>
                {["Tiêu đề", "Chế độ", "Trạng thái", "Ngày tạo", "Hành động"].map((h) => (
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
                  <td style={{ padding: "12px 14px" }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>{p.title}</div>
                    <div
                      style={{
                        fontSize: 11,
                        color: theme.textDim,
                        fontFamily: "monospace",
                        marginTop: 2,
                      }}
                    >
                      {p.id.slice(0, 8)}…
                    </div>
                  </td>
                  <td style={{ padding: "12px 14px", fontSize: 12 }}>
                    <Badge tone="info">{p.quality_mode}</Badge>
                  </td>
                  <td style={{ padding: "12px 14px", fontSize: 12 }}>
                    <StatusDot status={p.status} />
                    <span style={{ marginLeft: 4, textTransform: "capitalize" }}>{p.status}</span>
                  </td>
                  <td
                    style={{
                      padding: "12px 14px",
                      fontSize: 12,
                      color: theme.textMuted,
                      fontVariantNumeric: "tabular-nums",
                    }}
                  >
                    {new Date(p.created_at).toLocaleString()}
                  </td>
                  <td style={{ padding: "12px 14px" }}>
                    <div style={{ display: "flex", gap: 6, justifyContent: "flex-end" }}>
                      <Button
                        size="sm"
                        variant="primary"
                        onClick={() => router.push(`/projects/${p.id}/workspace`)}
                      >
                        🖥 Workspace
                      </Button>
                      <Button
                        size="sm"
                        onClick={() => router.push(`/projects/${p.id}/upload`)}
                      >
                        📤 Upload
                      </Button>
                      <Button
                        size="sm"
                        variant="danger"
                        title="Xóa project vĩnh viễn"
                        onClick={() => setPendingDelete(p)}
                      >
                        🗑 Xóa
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      <Modal
        open={!!pendingDelete}
        onClose={() => {
          if (!deleting) {
            setPendingDelete(null);
            setDeleteError(null);
          }
        }}
        title="Xóa project?"
      >
        {pendingDelete && (
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <p style={{ margin: 0, fontSize: 13, color: theme.text }}>
              Bạn có chắc chắn muốn xóa project{" "}
              <strong style={{ color: theme.accent }}>{pendingDelete.title}</strong>?
            </p>
            <p
              style={{
                margin: 0,
                fontSize: 12,
                color: theme.textMuted,
                background: "#450a0a",
                border: "1px solid #7f1d1d",
                borderRadius: 6,
                padding: 10,
              }}
            >
              ⚠ Hành động này sẽ xóa tất cả video, bản ghi, bản dịch, giọng nói và
              workflow đang chạy. Không thể hoàn tác.
            </p>
            {deleteError && (
              <div
                style={{
                  background: "#450a0a",
                  color: theme.danger,
                  padding: "8px 10px",
                  borderRadius: 6,
                  fontSize: 12,
                  border: "1px solid #7f1d1d",
                }}
              >
                ❌ {deleteError}
              </div>
            )}
            <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4 }}>
              <Button
                onClick={() => {
                  setPendingDelete(null);
                  setDeleteError(null);
                }}
                disabled={deleting}
              >
                Huỷ
              </Button>
              <Button variant="danger" onClick={confirmDelete} disabled={deleting}>
                {deleting ? "⏳ Đang xóa…" : "🗑 Xóa vĩnh viễn"}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
