import dynamic from "next/dynamic";

const RequireOwner = dynamic(() => import("@/components/RequireOwner").then((m) => m.RequireOwner), { ssr: false });

export default function AdminIndex() {
  return (
    <RequireOwner>
      <div style={{ padding: 24 }}>
        <h1 style={{ fontSize: 22, margin: 0 }}>Admin overview</h1>
        <p style={{ color: "#94a3b8", marginTop: 8 }}>Chọn một mục bên trái: Audit, Voice, hoặc Dataset.</p>
      </div>
    </RequireOwner>
  );
}
