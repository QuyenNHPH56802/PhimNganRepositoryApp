"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import { loadToken } from "@web/lib/auth";

interface AuditItem {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  payload: Record<string, unknown> | null;
  created_at: string;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "/api";

export default function ProjectAuditPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const [items, setItems] = useState<AuditItem[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      const token = loadToken();
      if (!token) return;
      const response = await fetch(`${API_BASE}/projects/${projectId}/audit`, {
        headers: { Authorization: `Bearer ${token}` },
        cache: "no-store",
      });
      if (!response.ok) {
        setError(`audit fetch failed: ${response.status}`);
        return;
      }
      const payload = (await response.json()) as { items: AuditItem[] };
      setItems(payload.items ?? []);
    }
    void load();
  }, [projectId]);

  return (
    <section>
      <h1 style={{ fontSize: 20, marginBottom: 12 }}>Audit log</h1>
      {error && <p style={{ color: "#f87171" }}>{error}</p>}
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th align="left">Time</th>
            <th align="left">Action</th>
            <th align="left">Entity</th>
            <th align="left">Payload</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id}>
              <td>{new Date(item.created_at).toLocaleString()}</td>
              <td>{item.action}</td>
              <td>{item.entity_type}:{item.entity_id}</td>
              <td><code>{JSON.stringify(item.payload ?? {})}</code></td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}