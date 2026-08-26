"use client";

import { useRouter } from "next/navigation";

export const SUPPORTED_LOCALES = ["vi", "en", "zh", "ja", "ko", "fr", "de", "es", "pt", "th"] as const;

export function LocaleSwitcher({ current }: { current: string }) {
  const router = useRouter();
  async function change(locale: string) {
    await fetch("/api/locale", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ locale }) });
    router.refresh();
  }
  return (
    <select value={current} onChange={(e) => change(e.target.value)} className="border rounded px-2 py-1 text-sm">
      {SUPPORTED_LOCALES.map((code) => (
        <option key={code} value={code}>{code.toUpperCase()}</option>
      ))}
    </select>
  );
}