"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Button, Card, EmptyState, Input, Modal } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";
import {
  createWebhook,
  deleteWebhook,
  listDeliveries,
  listWebhooks,
  testWebhook,
  toggleWebhook,
  type Webhook,
  type WebhookDelivery,
  type WebhookEvent,
} from "@/lib/webhooks";

const EVENT_LABELS: Record<string, string> = {
  "workflow.completed": "Workflow hoàn tất",
  "workflow.failed": "Workflow thất bại",
  "workflow.progress": "Tiến trình workflow",
  "render.ready": "Video render xong",
  "translation.ready": "Bản dịch sẵn sàng",
};

export default function WebhooksSettingsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [webhooks, setWebhooks] = useState<Webhook[]>([]);
  const [availableEvents, setAvailableEvents] = useState<WebhookEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);
  const [selectedHook, setSelectedHook] = useState<Webhook | null>(null);
  const [deliveries, setDeliveries] = useState<WebhookDelivery[]>([]);
  const [testing, setTesting] = useState(false);
  const [saving, setSaving] = useState(false);

  // Add-form state.
  const [formUrl, setFormUrl] = useState("");
  const [formDesc, setFormDesc] = useState("");
  const [formEvents, setFormEvents] = useState<string[]>([]);
  const [formSecret, setFormSecret] = useState("");

  async function refresh() {
    // We need a project to fetch webhooks — if none selected, just load an empty list.
    setLoading(false);
  }

  useEffect(() => {
    refresh();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleAdd(projectId: string) {
    if (!formUrl.trim()) {
      toast("Cần nhập URL webhook", "warn");
      return;
    }
    setSaving(true);
    try {
      await createWebhook(projectId, {
        url: formUrl.trim(),
        description: formDesc.trim() || undefined,
        events: formEvents,
        secret: formSecret.trim() || undefined,
      });
      toast("Đã tạo webhook", "success");
      setShowAdd(false);
      setFormUrl("");
      setFormDesc("");
      setFormEvents([]);
      setFormSecret("");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(projectId: string, hook: Webhook) {
    if (!window.confirm(`Xoá webhook "${hook.url}"?`)) return;
    try {
      await deleteWebhook(projectId, hook.id);
      setWebhooks((prev) => prev.filter((h) => h.id !== hook.id));
      toast("Đã xoá webhook", "info");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  async function handleToggle(projectId: string, hook: Webhook) {
    try {
      const updated = await toggleWebhook(projectId, hook.id);
      setWebhooks((prev) => prev.map((h) => (h.id === hook.id ? updated : h)));
      toast(updated.is_active ? "Webhook đã bật" : "Webhook đã tắt", "info");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  async function handleTest(projectId: string, hook: Webhook) {
    setTesting(true);
    try {
      const result = await testWebhook(projectId, hook.id);
      if (result.success) {
        toast(`Test thành công — HTTP ${result.status_code}`, "success");
      } else {
        toast(`Test thất bại — ${result.last_error ?? `HTTP ${result.status_code}`}`, "warn");
      }
      setSelectedHook(hook);
      const hist = await listDeliveries(projectId, hook.id);
      setDeliveries(hist);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setTesting(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>🔗 Webhook Notifications</h1>
          <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0", maxWidth: 640 }}>
            Nhận thông báo qua HTTP POST khi workflow hoàn tất, render xong, hoặc có lỗi.
            Hữu ích để tích hợp Slack, Discord, hoặc hệ thống nội bộ.
          </p>
        </div>
        <Button variant="primary" onClick={() => setShowAdd(true)}>
          + Thêm webhook
        </Button>
      </header>

      {/* Info card */}
      <Card title="Các sự kiện được hỗ trợ" padded>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 8 }}>
          {availableEvents.length === 0 ? (
            <p style={{ fontSize: 13, color: theme.textMuted, margin: 0 }}>
              Đang tải…
            </p>
          ) : (
            availableEvents.map((ev) => (
              <span
                key={ev.id}
                style={{
                  fontSize: 12,
                  padding: "3px 10px",
                  borderRadius: 4,
                  background: theme.bgElevated,
                  border: `1px solid ${theme.border}`,
                  color: theme.text,
                }}
              >
                {EVENT_LABELS[ev.id] ?? ev.id}
              </span>
            ))
          )}
        </div>
      </Card>

      {/* Hooks list */}
      {webhooks.length === 0 && !loading ? (
        <EmptyState
          title="Chưa có webhook"
          description="Thêm webhook đầu tiên để nhận thông báo khi workflow hoàn tất hoặc có lỗi."
          action={
            <Button variant="primary" onClick={() => setShowAdd(true)}>
              + Thêm webhook đầu tiên
            </Button>
          }
        />
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {webhooks.map((hook) => (
            <Card key={hook.id} padded>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 12 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                      <span
                        style={{
                          width: 8,
                          height: 8,
                          borderRadius: 999,
                          background: hook.is_active ? theme.success : theme.textDim,
                          boxShadow: hook.is_active ? `0 0 6px ${theme.success}` : "none",
                          flexShrink: 0,
                        }}
                      />
                      <span
                        style={{
                          fontFamily: "ui-monospace, monospace",
                          fontSize: 13,
                          fontWeight: 600,
                          wordBreak: "break-all",
                        }}
                      >
                        {hook.url}
                      </span>
                    </div>
                    {hook.description && (
                      <p style={{ margin: "0 0 4px", fontSize: 12, color: theme.textMuted }}>
                        {hook.description}
                      </p>
                    )}
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                      {hook.events.map((ev) => (
                        <span
                          key={ev}
                          style={{
                            fontSize: 10,
                            padding: "1px 6px",
                            borderRadius: 3,
                            background: "rgba(125,211,252,0.08)",
                            border: `1px solid rgba(125,211,252,0.2)`,
                            color: theme.accent,
                          }}
                        >
                          {EVENT_LABELS[ev] ?? ev}
                        </span>
                      ))}
                    </div>
                    <div style={{ fontSize: 11, color: theme.textDim, marginTop: 6 }}>
                      Secret: <code>{hook.secret_preview}</code> &nbsp;·&nbsp;
                      Tạo: {new Date(hook.created_at).toLocaleString()}
                    </div>
                  </div>
                  <div style={{ display: "flex", gap: 8, flexShrink: 0 }}>
                    <Button
                      size="sm"
                      variant={hook.is_active ? "ghost" : "primary"}
                      onClick={() => handleToggle("demo-project", hook)}
                    >
                      {hook.is_active ? "Tắt" : "Bật"}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleTest("demo-project", hook)}
                      disabled={testing}
                    >
                      {testing ? "…" : "🧪 Test"}
                    </Button>
                    <Button
                      size="sm"
                      variant="danger"
                      onClick={() => handleDelete("demo-project", hook)}
                    >
                      🗑
                    </Button>
                  </div>
                </div>

                {/* Recent deliveries for selected hook */}
                {selectedHook?.id === hook.id && deliveries.length > 0 && (
                  <div
                    style={{
                      borderTop: `1px solid ${theme.border}`,
                      paddingTop: 10,
                      marginTop: 4,
                    }}
                  >
                    <div
                      style={{
                        fontSize: 11,
                        fontWeight: 700,
                        color: theme.textMuted,
                        textTransform: "uppercase",
                        marginBottom: 8,
                      }}
                    >
                      Lịch sử gửi (mới nhất)
                    </div>
                    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
                      {deliveries.slice(0, 5).map((d) => (
                        <div
                          key={d.id}
                          style={{
                            display: "flex",
                            gap: 10,
                            fontSize: 12,
                            alignItems: "center",
                            padding: "4px 8px",
                            background: theme.bgElevated,
                            borderRadius: 4,
                          }}
                        >
                          <span
                            style={{
                              width: 6,
                              height: 6,
                              borderRadius: 999,
                              background: d.success ? theme.success : theme.danger,
                              flexShrink: 0,
                            }}
                          />
                          <span style={{ color: theme.textMuted, flexShrink: 0 }}>
                            {d.event}
                          </span>
                          <span style={{ color: d.success ? theme.success : theme.danger }}>
                            {d.status_code ?? 0}
                          </span>
                          {d.last_error && (
                            <span style={{ color: theme.textDim, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                              {d.last_error}
                            </span>
                          )}
                          <span style={{ color: theme.textDim, marginLeft: "auto", flexShrink: 0 }}>
                            {new Date(d.created_at).toLocaleString()}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* Add webhook modal */}
      <Modal
        open={showAdd}
        onClose={() => setShowAdd(false)}
        title="Thêm Webhook"
        width={480}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 600 }}>URL endpoint *</span>
            <Input
              value={formUrl}
              onChange={(e) => setFormUrl(e.target.value)}
              placeholder="https://your-server.com/webhook"
              autoFocus
            />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 600 }}>Mô tả (tuỳ chọn)</span>
            <Input
              value={formDesc}
              onChange={(e) => setFormDesc(e.target.value)}
              placeholder="VD: Slack #alerts"
            />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 600 }}>Sự kiện</span>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {SUPPORTED_EVENTS.map((ev) => (
                <label key={ev} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
                  <input
                    type="checkbox"
                    checked={formEvents.includes(ev)}
                    onChange={(e) => {
                      setFormEvents((prev) =>
                        e.target.checked ? [...prev, ev] : prev.filter((x) => x !== ev),
                      );
                    }}
                  />
                  {EVENT_LABELS[ev] ?? ev}
                </label>
              ))}
            </div>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 600 }}>Secret (tuỳ chọn — tự động tạo nếu trống)</span>
            <Input
              value={formSecret}
              onChange={(e) => setFormSecret(e.target.value)}
              placeholder="min 16 ký tự"
              type="password"
            />
          </label>
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <Button variant="ghost" onClick={() => setShowAdd(false)}>Huỷ</Button>
            <Button
              variant="primary"
              onClick={() => handleAdd("demo-project")}
              disabled={saving}
            >
              {saving ? "…" : "Tạo webhook"}
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  );
}

const SUPPORTED_EVENTS = [
  "workflow.completed",
  "workflow.failed",
  "workflow.progress",
  "render.ready",
  "translation.ready",
];
