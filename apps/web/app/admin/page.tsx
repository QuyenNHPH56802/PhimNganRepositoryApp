import { RequireOwner } from "@/components/RequireOwner";

export default function AdminIndex() {
  return (
    <RequireOwner>
      <div className="p-6 space-y-2">
        <h1 className="text-2xl font-semibold">Admin overview</h1>
        <p className="text-gray-600">Chọn một mục bên trái: Audit, Voice, hoặc Dataset.</p>
      </div>
    </RequireOwner>
  );
}