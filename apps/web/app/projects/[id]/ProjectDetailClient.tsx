"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { Badge, Button, Card, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";

type WorkflowStep = {
  id: string;
  name: string;
  status: string;
  attempt: number;
  progress_pct: number;
  progress_message?: string | null;
};

type Workflow = {
  workflow_id: string;
  run_id: string;
  status: string;
};

export default function ProjectDetailClient({ projectId }: { projectId: string }) {
  const router = useRouter();
  const [project, setProject] = useState<{ title: string; status: string; quality_mode: string } | null>(null);
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    try {
      const p = await api.getProject(projectId);
      setProject({ title: p.title, status: p.status, quality_mode: p.quality_mode });
      try {
        const wf = await api.getWorkflow(projectId, projectId);
        setWorkflow(wf);
        const stepRows = await api.listWorkflowSteps(projectId, projectId);
        setSteps(stepRows);
      } catch {
        // no workflow yet
      }
      setError(null);
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}` : String(err));
    }
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [projectId]);

  async function triggerWorkflow(quality: "fast" | "balanced" | "high") {
    try {
      await api.triggerWorkflow(projectId, { quality_mode: quality });
      refresh();
    } catch (err) {
      setError(err instanceof ApiError ? `${err.status}: ${JSON.stringify(err.detail)}` : String(err));
    }
  }

  return (
    <div style={{ padding: 24, display: "flex", flexDirection: "column", gap: 16 }}>
      <header style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
        <div>
          <h1 style={{ margin: 0, fontSize: 22 }}>{project?.title ?? `Project ${projectId.slice(0, 8)}`}</h1>
          <p style={{ margin: "4px 0 0", color: theme.textMuted, fontSize: 12 }}>
            ID: {projectId} • Quality: {project?.quality_mode ?? "—"}
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Button onClick={() => router.push(`/projects/${projectId}/workspace`)} variant="primary">
            Mở Workspace →
          </Button>
        </div>
      </header>

      <Card title="Workflow">
        {!workflow ? (
          <div style={{ padding: 16, display: "flex", gap: 8, alignItems: "center" }}>
            <span style={{ color: theme.textMuted, fontSize: 13 }}>Chưa chạy workflow.</span>
            <div style={{ marginLeft: "auto", display: "flex", gap: 6 }}>
              <Button onClick={() => triggerWorkflow("fast")}>Fast</Button>
              <Button onClick={() => triggerWorkflow("balanced")} variant="primary">Balanced</Button>
              <Button onClick={() => triggerWorkflow("high")}>High</Button>
            </div>
          </div>
        ) : (
          <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 8 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13 }}>
              <StatusDot status={workflow.status} />
              <strong>{workflow.status}</strong>
              <span style={{ color: theme.textMuted, fontSize: 11 }}>id: {workflow.workflow_id}</span>
            </div>
          </div>
        )}
      </Card>

      <Card title="Steps">
        {steps.length === 0 ? (
          <div style={{ padding: 16, color: theme.textMuted, fontSize: 13 }}>
            Workflow chưa chạy hoặc chưa có steps.
          </div>
        ) : (
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["Step", "Status", "Progress"].map((h) => (
                  <th
                    key={h}
                    style={{ textAlign: "left", padding: "8px 12px", fontSize: 11, color: theme.textMuted, borderBottom: `1px solid ${theme.border}` }}
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {steps.map((s) => (
                <tr key={s.id} style={{ borderBottom: `1px solid ${theme.border}` }}>
                  <td style={{ padding: "10px 12px", fontSize: 13 }}>{s.name}</td>
                  <td style={{ padding: "10px 12px", fontSize: 12 }}>
                    <Badge tone={s.status === "completed" ? "success" : s.status === "failed" ? "danger" : "info"}>
                      {s.status}
                    </Badge>
                  </td>
                  <td style={{ padding: "10px 12px" }}>
                    <div
                      style={{
                        background: theme.bgElevated,
                        borderRadius: 4,
                        overflow: "hidden",
                        width: 200,
                        height: 6,
                      }}
                    >
                      <div style={{ background: theme.accent, width: `${s.progress_pct}%`, height: "100%" }} />
                    </div>
                    <span style={{ fontSize: 11, color: theme.textMuted }}>{s.progress_pct}%</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </Card>

      {error && (
        <div style={{ background: "#450a0a", color: theme.danger, padding: 10, borderRadius: 6, fontSize: 12 }}>
          Lỗi: {error}
        </div>
      )}
    </div>
  );
}
