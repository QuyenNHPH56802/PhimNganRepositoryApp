"use client";

import { useEffect, useState } from "react";

type VoiceProfile = {
  id: string;
  project_id: string;
  speaker_id: string;
  consent_status: "pending" | "granted" | "revoked";
  reference_audio_key: string | null;
  consent_evidence_key: string | null;
};

export default function VoiceAdminPage() {
  const [items, setItems] = useState<VoiceProfile[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const response = await fetch("/api/admin/voice-profiles");
    if (!response.ok) {
      setError(`HTTP ${response.status}`);
      return;
    }
    setItems(await response.json());
  }

  useEffect(() => {
    load();
  }, []);

  async function transition(profile: VoiceProfile, next: "granted" | "revoked", evidence: string) {
    const response = await fetch(`/api/admin/voice-profiles/${profile.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ consent_status: next, consent_evidence_key: evidence || null }),
    });
    if (!response.ok) {
      setError(`transition failed: ${response.status} ${await response.text()}`);
      return;
    }
    setError(null);
    load();
  }

  return (
    <div className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Voice profiles</h1>
      {error && <p className="text-red-500 text-sm">{error}</p>}
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="p-2">Speaker</th>
            <th className="p-2">Project</th>
            <th className="p-2">Status</th>
            <th className="p-2">Reference</th>
            <th className="p-2">Action</th>
          </tr>
        </thead>
        <tbody>
          {items.map((profile) => (
            <tr key={profile.id} className="border-b">
              <td className="p-2">{profile.speaker_id}</td>
              <td className="p-2 text-xs">{profile.project_id}</td>
              <td className="p-2">{profile.consent_status}</td>
              <td className="p-2 text-xs">{profile.reference_audio_key ?? "—"}</td>
              <td className="p-2 space-x-2">
                {profile.consent_status !== "granted" && (
                  <button onClick={() => {
                    const evidence = window.prompt("Evidence key?") ?? "";
                    if (evidence) transition(profile, "granted", evidence);
                  }} className="bg-green-600 text-white px-2 py-1 rounded">Grant</button>
                )}
                {profile.consent_status !== "revoked" && (
                  <button onClick={() => transition(profile, "revoked", "")} className="bg-red-600 text-white px-2 py-1 rounded">Revoke</button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}