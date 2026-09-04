"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Button, Card, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";
import { getQualityReport, type QualityReport, type SegmentScore } from "@/lib/quality";

const ISSUE_LABELS: Record<string, string> = {
  length_ratio_low: "Tỉ lệ thấp",
  length_ratio_high: "Tỉ lệ cao",
  glossary_miss: "Thiếu thuật ngữ",
  pinyin_leak: "Pinyin lộ",
  untranslated: "Còn Hán tự",
  empty: "Trống",
};

export default function QualityDashboard() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const [report, setReport] = useState<QualityReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "fail" | "warn">("all");

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await getQualityReport(projectId);
      setReport(r);
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  const filtered = report?.segments.filter((s) => {
    if (filter === "fail") return s.qa_status === "fail";
    if (filter === "warn") return s.qa_status === "warn";
    return true;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16, padding: 16 }}>
      <header
        style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 16 }}
      >
        <div>
          <h1 style={{ fontSize: 20, margin: 0 }}>📋 Báo cáo chất lượng dịch</h1>
          <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0" }}>
            Điểm chất lượng cho từng segment — tập trung vào các segment có lỗi trước.
          </p>
        </div>
        <Button onClick={fetch} disabled={loading}>
          {loading ? "⏳ Đang tải…" : "🔄 Làm mới"}
        </Button>
      </header>

      {loading && !report && (
        <div style={{ color: theme.textMuted, fontSize: 13, padding: 20 }}>
          Đang chạy QA trên {report?.total_segments ?? "…"} segments…
        </div>
      )}

      {error && (
        <Card title="Lỗi">
          <div style={{ padding: 12, color: theme.danger, fontSize: 13 }}>
            ❌ {error}
            <br />
            <span style={{ color: theme.textMuted }}>
              Kiểm tra: (1) đã chạy translation chưa, (2) transcript đã load chưa.
            </span>
          </div>
        </Card>
      )}

      {report && (
        <>
          {/* Summary */}
          <section
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(4, minmax(0,1fr))",
              gap: 12,
            }}
          >
            <SummaryCard
              label="Tổng segment"
              value={report.total_segments}
              color={theme.text}
            />
            <SummaryCard
              label="Đạt (pass)"
              value={report.passed_segments}
              color={theme.success}
            />
            <SummaryCard
              label="Cảnh báo"
              value={report.warning_segments}
              color={theme.warn}
            />
            <SummaryCard
              label="Thất bại"
              value={report.failed_segments}
              color={theme.danger}
            />
          </section>

          {/* Overall pass / fail banner */}
          <div
            style={{
              padding: "12px 16px",
              borderRadius: 8,
              background: report.overall_passed
                ? "rgba(34,197,94,0.1)"
                : "rgba(239,68,68,0.1)",
              border: `1px solid ${report.overall_passed ? theme.success : theme.danger}`,
              display: "flex",
              alignItems: "center",
              gap: 12,
            }}
          >
            <StatusDot status={report.overall_passed ? "completed" : "failed"} />
            <div>
              <strong style={{ color: report.overall_passed ? theme.success : theme.danger }}>
                {report.overall_passed ? "✓ Tất cả segment đạt chuẩn" : "✗ Có segment thất bại"}
              </strong>
              {report.stats && (
                <div style={{ fontSize: 12, color: theme.textMuted, marginTop: 4 }}>
                  Tỉ lệ dịch: {report.stats.ratio_min?.toFixed(2) ?? "?"}–{report.stats.ratio_max?.toFixed(2) ?? "?"} &nbsp;·&nbsp;
                  Pinyin lộ: {report.stats.pinyin_leak_count} &nbsp;·&nbsp;
                  Còn Hán tự: {report.stats.untranslated_count} &nbsp;·&nbsp;
                  Thiếu thuật ngữ: {report.stats.glossary_misses}
                </div>
              )}
            </div>
          </div>

          {/* Filter */}
          <div style={{ display: "flex", gap: 8 }}>
            {(["all", "fail", "warn"] as const).map((f) => (
              <Button
                key={f}
                size="sm"
                variant={filter === f ? "primary" : "ghost"}
                onClick={() => setFilter(f)}
              >
                {f === "all" ? `Tất cả (${report.total_segments})` : f === "fail" ? `Thất bại (${report.failed_segments})` : `Cảnh báo (${report.warning_segments})`}
              </Button>
            ))}
          </div>

          {/* Segment list */}
          <Card title={`Danh sách segment (${filtered?.length ?? 0})`} padded={false}>
            <div role="table" aria-label="Danh sách segment chất lượng">
              <div
                role="row"
                style={{
                  display: "grid",
                  gridTemplateColumns: "50px 1fr 1fr 120px",
                  gap: 12,
                  padding: "10px 14px",
                  borderBottom: `1px solid ${theme.border}`,
                  background: "#0d172e",
                  fontSize: 11,
                  fontWeight: 700,
                  textTransform: "uppercase",
                  color: theme.textMuted,
                }}
              >
                <span>#</span>
                <span>Nguồn (ZH)</span>
                <span>Bản dịch (VI)</span>
                <span>Vấn đề</span>
              </div>
              {filtered?.map((seg) => (
                <SegmentRow key={seg.segment_id} segment={seg} />
              ))}
              {filtered?.length === 0 && (
                <div style={{ padding: 16, textAlign: "center", color: theme.textMuted, fontSize: 13 }}>
                  Không có segment nào trong bộ lọc này.
                </div>
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <Card padded>
      <div style={{ fontSize: 11, color: theme.textMuted, textTransform: "uppercase", letterSpacing: 0.5 }}>{label}</div>
      <div style={{ fontSize: 28, fontWeight: 700, marginTop: 4, color }}>{value}</div>
    </Card>
  );
}

function SegmentRow({ segment }: { segment: SegmentScore }) {
  const [expanded, setExpanded] = useState(false);
  const statusColor =
    segment.qa_status === "fail" ? theme.danger : segment.qa_status === "warn" ? theme.warn : theme.success;

  return (
    <div
      role="row"
      style={{
        borderBottom: `1px solid ${theme.border}`,
        padding: "10px 14px",
        display: "flex",
        flexDirection: "column",
        gap: 6,
        background: segment.qa_status !== "pass" ? `${statusColor}08` : "transparent",
      }}
    >
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "50px 1fr 1fr 120px",
          gap: 12,
          alignItems: "center",
          cursor: segment.issues.length > 0 ? "pointer" : "default",
        }}
        onClick={() => segment.issues.length > 0 && setExpanded((v) => !v)}
      >
        <span style={{ fontSize: 12, color: theme.textMuted, fontFamily: "ui-monospace" }}>
          #{segment.idx}
        </span>
        <span
          style={{
            fontSize: 13,
            fontFamily: "ui-monospace",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
          title={segment.source_text}
        >
          {segment.source_text}
        </span>
        <span
          style={{
            fontSize: 13,
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
          title={segment.display_text}
        >
          {segment.display_text}
        </span>
        <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
          {segment.issues.map((issue) => (
            <span
              key={issue.kind}
              style={{
                fontSize: 10,
                padding: "1px 6px",
                borderRadius: 4,
                background: issue.severity === "error" ? "rgba(239,68,68,0.15)" : "rgba(245,158,11,0.15)",
                color: issue.severity === "error" ? theme.danger : theme.warn,
                fontWeight: 600,
              }}
              title={issue.message}
            >
              {ISSUE_LABELS[issue.kind] ?? issue.kind}
            </span>
          ))}
          {segment.issues.length === 0 && (
            <span style={{ fontSize: 11, color: theme.success }}>✓ OK</span>
          )}
        </div>
      </div>
      {expanded && segment.issues.length > 0 && (
        <div
          style={{
            background: theme.bgElevated,
            borderRadius: 4,
            padding: "8px 12px",
            display: "flex",
            flexDirection: "column",
            gap: 4,
            marginLeft: 62,
          }}
        >
          {segment.issues.map((issue) => (
            <div key={issue.kind} style={{ fontSize: 12 }}>
              <strong
                style={{
                  color: issue.severity === "error" ? theme.danger : theme.warn,
                  marginRight: 8,
                }}
              >
                [{issue.severity}]
              </strong>
              <span style={{ color: theme.text }}>{ISSUE_LABELS[issue.kind] ?? issue.kind}:</span>{" "}
              <span style={{ color: theme.textMuted }}>{issue.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
