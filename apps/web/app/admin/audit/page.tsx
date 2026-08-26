"use client";

import { useMemo, useState } from "react";

type AuditItem = {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  actor: string;
  timestamp: string | null;
  payload: Record<string, unknown>;
};

export default function AuditPage() {
  const [entity, setEntity] = useState("");
  const [action, setAction] = useState("");
  const [actor, setActor] = useState("");
  const [items, setItems] = useState<AuditItem[]>([]);
  const query = useMemo(() => {
    const params = new URLSearchParams();
    if (entity) params.set("entity", entity);
    if (action) params.set("action", action);
    if (actor) params.set("actor", actor);
    return params.toString();
  }, [entity, action, actor]);

  async function load() {
    const response = await fetch(`/api/admin/audit-logs?${query}`);
    const body = await response.json();
    setItems(body.items ?? []);
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Audit log</h1>
      <div className="flex flex-wrap gap-2">
        <input value={entity} onChange={(e) => setEntity(e.target.value)} placeholder="entity_type" className="border px-2 py-1 rounded" />
        <input value={action} onChange={(e) => setAction(e.target.value)} placeholder="action" className="border px-2 py-1 rounded" />
        <input value={actor} onChange={(e) => setActor(e.target.value)} placeholder="actor" className="border px-2 py-1 rounded" />
        <button onClick={load} className="bg-blue-600 text-white px-3 py-1 rounded">Tải lại</button>
      </div>
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="p-2">Time</th>
            <th className="p-2">Entity</th>
            <th className="p-2">Action</th>
            <th className="p-2">Actor</th>
            <th className="p-2">Payload</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b">
              <td className="p-2">{item.timestamp}</td>
              <td className="p-2">{item.entity_type}</td>
              <td className="p-2">{item.action}</td>
              <td className="p-2">{item.actor}</td>
              <td className="p-2 text-xs text-gray-500">{JSON.stringify(item.payload)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}