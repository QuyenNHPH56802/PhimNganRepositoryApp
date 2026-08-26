import { ReactNode } from "react";
import Link from "next/link";

export default function AdminLayout({ children }: { children: ReactNode }) {
  return (
    <div className="grid grid-cols-[200px_1fr] min-h-screen">
      <aside className="bg-gray-50 border-r p-4 space-y-2">
        <h2 className="text-lg font-semibold">Admin</h2>
        <Link href="/admin/audit" className="block px-2 py-1 rounded hover:bg-gray-200">Audit log</Link>
        <Link href="/admin/voice" className="block px-2 py-1 rounded hover:bg-gray-200">Voice profiles</Link>
        <Link href="/admin/dataset" className="block px-2 py-1 rounded hover:bg-gray-200">Dataset</Link>
      </aside>
      <main>{children}</main>
    </div>
  );
}