"use client";

import { useEffect, useState } from "react";

type WorkflowStep = {
  id: string;
  name: string;
  status: string;
  attempt: number;
  progress_pct: number;
  progress_message: string | null;
  artifact_signature: string | null;
};

type Workflow = {
  workflow_id: string;
  run_id: string;
  status: string;
};

export default function ProjectDetailClient({ projectId }: { projectId: string }) {
  const [workflow, setWorkflow] = useState<Workflow | null>(null);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function refresh() {
    const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
    try {
      const wfRes = await fetch(`${base}/projects/${projectId}/workflows/${projectId}`, { cache: "no-store" });
      if (!wfRes.ok) {
        setError(`workflow ${wfRes.status}`);
        return;
      }
      const wfData = (await wfRes.json()) as Workflow;
      setWorkflow(wfData);
      const stepsRes = await fetch(`${base}/projects/${projectId}/workflows/${projectId}/steps`, { cache: "no-store" });
      if (stepsRes.ok) {
        const stepData = (await stepsRes.json()) as WorkflowStep[];
        setSteps(stepData);
      }
      setError(null);
    } catch {
      setError("API unreachable");
    }
  }

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 5000);
    return () => clearInterval(id);
  }, [projectId]);

  return (
    <section>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Project {projectId}</h1>
      <p style={{ color: "#94a3b8" }}>
        Workflow: {workflow ? `${workflow.workflow_id} (${workflow.status})` : "—"}
      </p>
      {error && <p style={{ color: "#f87171" }}>{error}</p>}
      <ul>
        <li><a href={`/projects/${projectId}/upload`} style={{ color: "#7dd3fc" }}>Upload asset</a></li>
      </ul>
      <h2 style={{ fontSize: 18, marginTop: 24, marginBottom: 8 }}>Steps</h2>
      {steps.length === 0 ? (
        <p>Chưa có step nào.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid #334155" }}>
              <th>Step</th>
              <th>Status</th>
              <th>Progress</th>
            </tr>
          </thead>
          <tbody>
            {steps.map((step) => (
              <tr key={step.id} style={{ borderBottom: "1px solid #1e293b" }}>
                <td>{step.name}</td>
                <td>{step.status}</td>
                <td>
                  <div style={{ background: "#0f172a", borderRadius: 4, overflow: "hidden", width: 200 }}>
                    <div style={{ background: "#0ea5e9", width: `${step.progress_pct}%`, height: 8 }} />
                  </div>
                  <span style={{ fontSize: 12, color: "#94a3b8" }}>{step.progress_pct}%</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}