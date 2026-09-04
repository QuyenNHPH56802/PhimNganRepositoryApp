"use client";

import { useEffect, useState, useCallback } from "react";
import { Button, Card, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";
import { loadToken } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

interface ProbeResult {
  name: string;
  description: string;
  status: "ok" | "warn" | "fail" | "pending";
  detail: string;
  durationMs?: number;
}

const PROBES: Array<{ key: string; name: string; description: string; run: () => Promise<Omit<ProbeResult, "name" | "description">> }> = [
  {
    key: "web",
    name: "Web (Next.js)",
    description: "Self — trang đang chạy.",
    run: async () => ({ status: "ok", detail: "Đang chạy trên trình duyệt", durationMs: 0 }),
  },
  {
    key: "backend_health",
    name: "Backend /healthz",
    description: "API server còn sống và trả 200.",
    run: async () => {
      const t0 = performance.now();
      try {
        const r = await fetch(`${API_BASE}/healthz`, { cache: "no-store" });
        const dt = Math.round(performance.now() - t0);
        if (r.ok) return { status: "ok", detail: `HTTP ${r.status}`, durationMs: dt };
        return { status: "fail", detail: `HTTP ${r.status}`, durationMs: dt };
      } catch (err) {
        return { status: "fail", detail: err instanceof Error ? err.message : String(err) };
      }
    },
  },
  {
    key: "backend_ready",
    name: "Backend /readyz",
    description: "API server sẵn sàng nhận request (DB + cache connected).",
    run: async () => {
      const t0 = performance.now();
      try {
        const r = await fetch(`${API_BASE}/readyz`, { cache: "no-store" });
        const dt = Math.round(performance.now() - t0);
        if (r.ok) return { status: "ok", detail: `HTTP ${r.status}`, durationMs: dt };
        return { status: "warn", detail: `HTTP ${r.status}`, durationMs: dt };
      } catch (err) {
        return { status: "fail", detail: err instanceof Error ? err.message : String(err) };
      }
    },
  },
  {
    key: "web_health",
    name: "Web /api/healthz",
    description: "Proxy qua Next.js (aggregate healthz + readyz).",
    run: async () => {
      const t0 = performance.now();
      try {
        const r = await fetch(`/api/healthz`, { cache: "no-store" });
        const dt = Math.round(performance.now() - t0);
        const body = await r.json();
        if (body.ok) return { status: "ok", detail: `Aggregate OK`, durationMs: dt };
        return { status: "warn", detail: `Aggregate degraded: ${JSON.stringify(body).slice(0, 80)}`, durationMs: dt };
      } catch (err) {
        return { status: "fail", detail: err instanceof Error ? err.message : String(err) };
      }
    },
  },
  {
    key: "openapi",
    name: "OpenAPI /openapi.json",
    description: "Endpoint docs (FastAPI auto-generated).",
    run: async () => {
      const t0 = performance.now();
      try {
        const r = await fetch(`${API_BASE}/openapi.json`, { cache: "no-store" });
        const dt = Math.round(performance.now() - t0);
        if (r.ok) return { status: "ok", detail: `HTTP ${r.status}`, durationMs: dt };
        return { status: "fail", detail: `HTTP ${r.status}`, durationMs: dt };
      } catch (err) {
        return { status: "fail", detail: err instanceof Error ? err.message : String(err) };
      }
    },
  },
  {
    key: "metrics",
    name: "Prometheus /metrics",
    description: "Metrics endpoint scrape được.",
    run: async () => {
      try {
        const r = await fetch(`${API_BASE}/metrics`, { cache: "no-store" });
        if (r.ok) {
          const text = await r.text();
          return { status: "ok", detail: `${text.split("\n").length} dòng` };
        }
        return { status: "fail", detail: `HTTP ${r.status}` };
      } catch (err) {
        return { status: "fail", detail: err instanceof Error ? err.message : String(err) };
      }
    },
  },
  {
    key: "admin_overview",
    name: "Admin /admin/overview",
    description: "API thống kê — yêu cầu Bearer token admin.",
    run: async () => {
      try {
        const token = loadToken();
        if (!token) return { status: "warn", detail: "Chưa đăng nhập (không có token)" };
        const r = await fetch(`${API_BASE}/admin/overview`, {
          headers: { Authorization: `Bearer ${token}` },
          cache: "no-store",
        });
        if (r.ok) return { status: "ok", detail: `HTTP ${r.status}` };
        if (r.status === 401 || r.status === 403) return { status: "warn", detail: `HTTP ${r.status} (token không hợp lệ)` };
        return { status: "fail", detail: `HTTP ${r.status}` };
      } catch (err) {
        return { status: "fail", detail: err instanceof Error ? err.message : String(err) };
      }
    },
  },
];

export default function HealthPage() {
  const [results, setResults] = useState<ProbeResult[]>([]);
  const [running, setRunning] = useState(false);
  const [lastRun, setLastRun] = useState<Date | null>(null);
  const toast = useToast();

  const runAll = useCallback(async () => {
    setRunning(true);
    // Mark all as pending first for instant UI feedback.
    setResults(PROBES.map((p) => ({ name: p.name, description: p.description, status: "pending", detail: "Đang kiểm tra…" })));
    const next: ProbeResult[] = [];
    for (const probe of PROBES) {
      try {
        const partial = await probe.run();
        next.push({ name: probe.name, description: probe.description, ...partial });
      } catch (err) {
        next.push({
          name: probe.name,
          description: probe.description,
          status: "fail",
          detail: err instanceof Error ? err.message : String(err),
        });
      }
      // Update progressively.
      setResults([...next, ...PROBES.slice(next.length).map((p) => ({ name: p.name, description: p.description, status: "pending" as const, detail: "Đang kiểm tra…" }))]);
    }
    setResults(next);
    setLastRun(new Date());
    setRunning(false);
    const failed = next.filter((r) => r.status === "fail").length;
    if (failed === 0) toast("Tất cả health check đều OK", "success");
    else toast(`${failed} probe thất bại — xem chi tiết bên dưới`, "warn");
  }, [toast]);

  useEffect(() => {
    runAll();
  }, [runAll]);

  const okCount = results.filter((r) => r.status === "ok").length;
  const warnCount = results.filter((r) => r.status === "warn").length;
  const failCount = results.filter((r) => r.status === "fail").length;
  const pendingCount = results.filter((r) => r.status === "pending").length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}>
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>🩺 System Health</h1>
          <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0", maxWidth: 640 }}>
            Probe các thành phần chính của platform (web, API, metrics, admin auth).
            Hữu ích khi debug "tại sao project không load được".
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          {lastRun && (
            <span style={{ fontSize: 11, color: theme.textMuted }}>
              Cập nhật lần cuối: {lastRun.toLocaleTimeString()}
            </span>
          )}
          <Button onClick={runAll} disabled={running}>
            {running ? "⏳ Đang kiểm tra…" : "🔄 Chạy lại"}
          </Button>
        </div>
      </header>

      <section style={{ display: "grid", gridTemplateColumns: "repeat(4, minmax(0, 1fr))", gap: 12 }}>
        <SummaryCard label="OK" value={okCount} color={theme.success} />
        <SummaryCard label="Cảnh báo" value={warnCount} color={theme.warn} />
        <SummaryCard label="Thất bại" value={failCount} color={theme.danger} />
        <SummaryCard label="Đang chạy" value={pendingCount} color={theme.textMuted} />
      </section>

      <Card title="Probes" padded={false}>
        <div role="table" aria-label="Danh sách health probe">
          <div
            role="row"
            style={{
              display: "grid",
              gridTemplateColumns: "minmax(180px, 1.5fr) 2fr 1fr 80px",
              gap: 12,
              padding: "10px 14px",
              borderBottom: `1px solid ${theme.border}`,
              background: "#0d172e",
              fontSize: 11,
              fontWeight: 700,
              textTransform: "uppercase",
              color: theme.textMuted,
              letterSpacing: 0.5,
            }}
          >
            <span>Tên</span>
            <span>Mô tả</span>
            <span>Trạng thái / Chi tiết</span>
            <span style={{ textAlign: "right" }}>Latency</span>
          </div>
          {results.map((r, i) => (
            <div
              role="row"
              key={r.name + i}
              style={{
                display: "grid",
                gridTemplateColumns: "minmax(180px, 1.5fr) 2fr 1fr 80px",
                gap: 12,
                padding: "10px 14px",
                borderBottom: `1px solid ${theme.border}`,
                fontSize: 13,
                alignItems: "center",
              }}
            >
              <span style={{ fontWeight: 600 }}>
                <StatusDot
                  status={
                    r.status === "ok"
                      ? "completed"
                      : r.status === "warn"
                        ? "processing"
                        : r.status === "fail"
                          ? "failed"
                          : "pending"
                  }
                />
                {r.name}
              </span>
              <span style={{ color: theme.textMuted, fontSize: 12 }}>{r.description}</span>
              <span
                style={{
                  fontSize: 12,
                  color:
                    r.status === "ok"
                      ? theme.success
                      : r.status === "warn"
                        ? theme.warn
                        : r.status === "fail"
                          ? theme.danger
                          : theme.textMuted,
                  fontFamily: "ui-monospace, monospace",
                }}
              >
                {r.detail}
              </span>
              <span
                style={{
                  textAlign: "right",
                  fontSize: 11,
                  color: theme.textDim,
                  fontFamily: "ui-monospace, monospace",
                }}
              >
                {r.durationMs !== undefined ? `${r.durationMs} ms` : "—"}
              </span>
            </div>
          ))}
          {results.length === 0 && (
            <div style={{ padding: 16, color: theme.textMuted, fontSize: 13, textAlign: "center" }}>
              Đang khởi tạo probe…
            </div>
          )}
        </div>
      </Card>

      <Card title="Mẹo debug" padded>
        <ul style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: theme.textMuted, display: "flex", flexDirection: "column", gap: 6 }}>
          <li>
            Nếu <strong style={{ color: theme.text }}>Backend /healthz</strong> fail: kiểm tra <code>docker compose ps</code> & container logs (<code>docker logs translator-api</code>).
          </li>
          <li>
            Nếu <strong style={{ color: theme.text }}>OpenAPI /openapi.json</strong> fail: server có thể đang restart sau khi sửa code — đợi 5–10s rồi thử lại.
          </li>
          <li>
            Nếu <strong style={{ color: theme.text }}>Admin /admin/overview</strong> trả 401: đăng nhập lại với tài khoản admin.
          </li>
          <li>
            Nếu <strong style={{ color: theme.text }}>Web /api/healthz</strong> warn: thường do backend down, xem logs worker.
          </li>
        </ul>
      </Card>
    </div>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <Card padded>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div>
          <div style={{ fontSize: 11, color: theme.textMuted, textTransform: "uppercase", letterSpacing: 0.6 }}>{label}</div>
          <div style={{ fontSize: 28, fontWeight: 700, marginTop: 4, color }}>{value}</div>
        </div>
      </div>
    </Card>
  );
}
