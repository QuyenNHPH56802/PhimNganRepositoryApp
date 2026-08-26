"use client";

import { useEffect, useRef, useState } from "react";

export type WorkflowStep = {
  id: string;
  name: string;
  status: "queued" | "processing" | "ready" | "failed";
  progress_pct: number;
  progress_message?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
};

export type WorkflowEvent = {
  type: "step_update" | "heartbeat";
  step?: WorkflowStep;
  timestamp?: string;
};

export function useWorkflowStream(workflowId: string): {
  steps: WorkflowStep[];
  status: "idle" | "connected" | "error";
} {
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [status, setStatus] = useState<"idle" | "connected" | "error">("idle");
  const queueRef = useRef<WorkflowStep[]>([]);

  useEffect(() => {
    if (!workflowId) return;
    let cancelled = false;
    let source: EventSource | null = null;
    const flush = () => {
      if (queueRef.current.length === 0) return;
      const incoming = queueRef.current.splice(0);
      setSteps((prev) => {
        const map = new Map<string, WorkflowStep>();
        for (const s of prev) map.set(s.name, s);
        for (const s of incoming) map.set(s.name, { ...map.get(s.name), ...s });
        return Array.from(map.values());
      });
    };
    const connect = () => {
      source = new EventSource(`/api/workflows/${workflowId}/events`);
      source.onopen = () => setStatus("connected");
      source.onerror = () => {
        if (cancelled) return;
        setStatus("error");
        source?.close();
        setTimeout(connect, 2000);
      };
      source.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data) as WorkflowEvent;
          if (payload.type === "step_update" && payload.step) {
            queueRef.current.push(payload.step);
            flush();
          }
        } catch {
          /* ignore */
        }
      };
    };
    connect();
    return () => {
      cancelled = true;
      source?.close();
    };
  }, [workflowId]);

  return { steps, status };
}