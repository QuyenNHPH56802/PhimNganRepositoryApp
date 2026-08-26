"use client";

import { useEffect, useState } from "react";

type Sentence = {
  id: string;
  zh: string;
  vi: string;
  domain: string;
  license: string;
  provenance?: { contributor?: string };
};

const LICENSE_OPTIONS = ["CC-BY-SA-4.0", "CC-BY-4.0", "CC0"] as const;
const DOMAIN_OPTIONS = ["news", "vlog", "review", "drama", "narration"] as const;

export default function DatasetAdminPage() {
  const [items, setItems] = useState<Sentence[]>([]);
  const [zh, setZh] = useState("");
  const [vi, setVi] = useState("");
  const [domain, setDomain] = useState<(typeof DOMAIN_OPTIONS)[number]>("vlog");
  const [license, setLicense] = useState<(typeof LICENSE_OPTIONS)[number]>("CC-BY-SA-4.0");
  const [contributor, setContributor] = useState("ops@team");
  const [error, setError] = useState<string | null>(null);

  async function load() {
    const response = await fetch("/api/admin/datasets");
    const body = await response.json();
    setItems(body.items ?? []);
  }

  useEffect(() => {
    load();
  }, []);

  async function submit() {
    setError(null);
    const response = await fetch("/api/admin/datasets/sentences", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: `web_${Date.now()}`,
        zh,
        vi,
        domain,
        license,
        provenance_contributor: contributor,
      }),
    });
    if (!response.ok) {
      setError(`HTTP ${response.status}: ${await response.text()}`);
      return;
    }
    setZh("");
    setVi("");
    load();
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-2xl font-semibold">Golden dataset</h1>
      <div className="grid grid-cols-2 gap-4">
        <label className="flex flex-col">
          <span>Source (zh)</span>
          <textarea value={zh} onChange={(e) => setZh(e.target.value)} className="border rounded p-2 min-h-[80px]" />
        </label>
        <label className="flex flex-col">
          <span>Reference (vi)</span>
          <textarea value={vi} onChange={(e) => setVi(e.target.value)} className="border rounded p-2 min-h-[80px]" />
        </label>
        <label className="flex flex-col">
          <span>Domain</span>
          <select value={domain} onChange={(e) => setDomain(e.target.value as typeof domain)} className="border rounded p-2">
            {DOMAIN_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col">
          <span>License</span>
          <select value={license} onChange={(e) => setLicense(e.target.value as typeof license)} className="border rounded p-2">
            {LICENSE_OPTIONS.map((opt) => (
              <option key={opt} value={opt}>{opt}</option>
            ))}
          </select>
        </label>
        <label className="flex flex-col">
          <span>Contributor</span>
          <input value={contributor} onChange={(e) => setContributor(e.target.value)} className="border rounded p-2" />
        </label>
      </div>
      <button onClick={submit} disabled={!zh || !vi} className="bg-blue-600 text-white px-4 py-2 rounded disabled:bg-gray-400">Thêm câu</button>
      {error && <p className="text-red-500">{error}</p>}
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="bg-gray-100 text-left">
            <th className="p-2">ID</th>
            <th className="p-2">ZH</th>
            <th className="p-2">VI</th>
            <th className="p-2">License</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-b">
              <td className="p-2 font-mono text-xs">{item.id}</td>
              <td className="p-2">{item.zh}</td>
              <td className="p-2">{item.vi}</td>
              <td className="p-2">{item.license}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}