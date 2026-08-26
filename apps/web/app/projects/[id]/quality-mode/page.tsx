"use client";

import { useState } from "react";

const MODES = [
  { id: "fast", label: "FAST", cps: 18, voiceClone: false },
  { id: "balanced", label: "BALANCED", cps: 16, voiceClone: false },
  { id: "high", label: "HIGH", cps: 14, voiceClone: true },
] as const;

export default function QualityModePage({ params }: { params: { id: string } }) {
  const [mode, setMode] = useState<typeof MODES[number]["id"]>("balanced");
  const [policy, setPolicy] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function apply(next: typeof mode) {
    setError(null);
    const response = await fetch(`/api/projects/${params.id}/quality-mode`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mode: next }),
    });
    if (!response.ok) {
      setError(`HTTP ${response.status}: ${await response.text()}`);
      return;
    }
    const body = await response.json();
    setMode(next);
    setPolicy(body.policy);
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Quality mode</h1>
      <div className="flex gap-3">
        {MODES.map((m) => (
          <button key={m.id} onClick={() => apply(m.id)} className={`px-4 py-2 rounded ${mode === m.id ? "bg-blue-600 text-white" : "border"}`}>
            {m.label}
          </button>
        ))}
      </div>
      {error && <p className="text-red-500">{error}</p>}
      {policy && (
        <pre className="bg-gray-100 p-3 rounded text-xs overflow-auto">{JSON.stringify(policy, null, 2)}</pre>
      )}
    </div>
  );
}