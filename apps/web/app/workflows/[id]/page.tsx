"use client";

import { useState } from "react";
import { useWorkflowStream, WorkflowStep } from "@/lib/useWorkflowStream";

export default function WorkflowProgressPage({ params }: { params: { id: string } }) {
  const { steps, status } = useWorkflowStream(params.id);
  const [cancelling, setCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function cancel() {
    setCancelling(true);
    setError(null);
    const response = await fetch(`/api/workflows/${params.id}/cancel`, { method: "POST" });
    if (!response.ok) {
      setError(`HTTP ${response.status}: ${await response.text()}`);
    }
    setCancelling(false);
  }

  return (
    <div className="p-6 space-y-4">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Workflow {params.id}</h1>
        <button onClick={cancel} disabled={cancelling} className="bg-red-600 text-white px-3 py-1 rounded disabled:bg-gray-400">
          {cancelling ? "Đang huỷ…" : "Huỷ workflow"}
        </button>
      </header>
      <p className="text-sm text-gray-500">Stream: {status}</p>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <ol className="space-y-2">
        {steps.map((step) => (
          <StepRow key={step.name} step={step} />
        ))}
      </ol>
    </div>
  );
}

function StepRow({ step }: { step: WorkflowStep }) {
  const color: Record<WorkflowStep["status"], string> = {
    queued: "bg-gray-200",
    processing: "bg-yellow-300",
    ready: "bg-green-500",
    failed: "bg-red-500",
  };
  return (
    <li className="border rounded p-3 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="font-medium">{step.name}</span>
        <span className={`px-2 py-0.5 text-xs rounded text-white ${color[step.status]}`}>{step.status}</span>
      </div>
      <div className="w-full bg-gray-100 h-2 rounded">
        <div className="bg-blue-500 h-2 rounded" style={{ width: `${step.progress_pct}%` }} />
      </div>
      {step.progress_message && <p className="text-xs text-gray-500">{step.progress_message}</p>}
    </li>
  );
}