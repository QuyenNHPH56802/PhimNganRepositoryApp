type QualityMode = "fast" | "balanced" | "high";

type Project = {
  id: string;
  title: string;
  quality_mode: QualityMode;
  status: string;
  created_at: string;
};

async function getProjects(): Promise<Project[]> {
  const base = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
  try {
    const res = await fetch(`${base}/projects`, { cache: "no-store" });
    if (!res.ok) return [];
    const data = (await res.json()) as { items: Project[] };
    return data.items;
  } catch {
    return [];
  }
}

export default async function DashboardPage() {
  const projects = await getProjects();
  return (
    <section>
      <h1 style={{ fontSize: 24, marginBottom: 16 }}>Dashboard</h1>
      <p style={{ color: "#94a3b8" }}>Phase 1 scaffold — dữ liệu sẽ kết nối API ở Phase 2.</p>
      {projects.length === 0 ? (
        <p>Chưa có project nào. Tạo project mới từ menu.</p>
      ) : (
        <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 16 }}>
          <thead>
            <tr style={{ textAlign: "left", borderBottom: "1px solid #334155" }}>
              <th>Title</th>
              <th>Quality Mode</th>
              <th>Status</th>
              <th>Created</th>
            </tr>
          </thead>
          <tbody>
            {projects.map((p) => (
              <tr key={p.id} style={{ borderBottom: "1px solid #1e293b" }}>
                <td><a href={`/projects/${p.id}`} style={{ color: "#7dd3fc" }}>{p.title}</a></td>
                <td>{p.quality_mode}</td>
                <td>{p.status}</td>
                <td>{new Date(p.created_at).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}