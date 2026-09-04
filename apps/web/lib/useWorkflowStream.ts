"use client";

import { useEffect, useRef, useState } from "react";
import type { WorkflowStep as SharedWorkflowStep } from "./types";

// The backend streams `step_update` events whose payload mirrors the
// WorkflowStep schema, plus heartbeats. Reuse the shared type and extend it
// locally with status-specific values (the SSE side uses snake_case strings
// already present in WorkflowStep.status).
export type WorkflowStep = SharedWorkflowStep;
export type { SharedWorkflowStep };

export type WorkflowEvent = {
  type: "step_update" | "heartbeat" | "error";
  step?: WorkflowStep;
  error?: string;
  timestamp?: string;
};

export function useWorkflowStream(workflowId: string | null): {
  steps: WorkflowStep[];
  status: "idle" | "connected" | "error";
  retryCount: number;
  error: string | null;
  events: WorkflowEvent[];
  lastError: string | null;
} {
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [status, setStatus] = useState<"idle" | "connected" | "error">("idle");
  const [retryCount, setRetryCount] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [events, setEvents] = useState<WorkflowEvent[]>([]);
  const [lastError, setLastError] = useState<string | null>(null);
  const queueRef = useRef<WorkflowStep[]>([]);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const retryCountRef = useRef(0);
  const MAX_RETRIES = 10;
  const MAX_DELAY_MS = 30000;

  const backoffDelay = (attempt: number) => Math.min(1000 * Math.pow(2, attempt), MAX_DELAY_MS);

  useEffect(() => {
    // Early validation: don't connect if workflowId is empty or invalid
    if (!workflowId || workflowId.trim() === "") {
      setStatus("idle");
      setSteps([]);
      setError(null);
      setEvents([]);
      setLastError(null);
      return;
    }
    let cancelled = false;
    let source: EventSource | null = null;
    retryCountRef.current = 0;
    setRetryCount(0);
    setError(null);

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
      if (cancelled) return;
      source = new EventSource(`/api/workflows/${workflowId}/events`);
      source.onopen = () => {
        if (cancelled) return;
        retryCountRef.current = 0;
        setRetryCount(0);
        setError(null);
        setStatus("connected");
      };
      source.onerror = (e) => {
        if (cancelled) return;
        source?.close();
        const errorMsg = `EventSource error on workflow ${workflowId}`;
        console.error(errorMsg, e);
        
        if (retryCountRef.current >= MAX_RETRIES) {
          const finalError = "Stream failed after 10 retries — kiểm tra trạng thái backend / workflow.";
          setStatus("error");
          setError(finalError);
          setLastError(finalError);
          return;
        }
        retryCountRef.current += 1;
        setRetryCount(retryCountRef.current);
        setStatus("error");
        const retryError = `Mất kết nối stream (lần thử ${retryCountRef.current}/${MAX_RETRIES})`;
        setError(retryError);
        setLastError(retryError);
        reconnectTimerRef.current = setTimeout(connect, backoffDelay(retryCountRef.current - 1));
      };
      source.onmessage = (event) => {
        if (cancelled) return;
        try {
          const payload = JSON.parse(event.data) as WorkflowEvent;
          setEvents((prev) => [...prev, payload]);
          
          if (payload.type === "step_update" && payload.step) {
            queueRef.current.push(payload.step);
            flush();
          } else if (payload.type === "error" && payload.error) {
            setError(payload.error);
            setLastError(payload.error);
          }
        } catch (err) {
          console.error("Failed to parse SSE message:", err);
        }
      };
    };

    connect();

    return () => {
      cancelled = true;
      source?.close();
      if (reconnectTimerRef.current) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
    };
  }, [workflowId]);

  return { steps, status, retryCount, error, events, lastError };
}