export const metadata = {
  title: "Translator",
  description: "Chinese -> Vietnamese video localization platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi">
      <body style={{ fontFamily: "system-ui, -apple-system, sans-serif", margin: 0, background: "#0f172a", color: "#e2e8f0" }}>
        <header style={{ padding: "16px 24px", borderBottom: "1px solid #1e293b", display: "flex", justifyContent: "space-between" }}>
          <strong>Translator</strong>
          <nav style={{ display: "flex", gap: 16 }}>
            <a href="/" style={{ color: "#e2e8f0" }}>Dashboard</a>
            <a href="/projects/new" style={{ color: "#e2e8f0" }}>New Project</a>
            <a href="/settings" style={{ color: "#e2e8f0" }}>Settings</a>
            <a href="/login" style={{ color: "#e2e8f0" }}>Login</a>
          </nav>
        </header>
        <main style={{ padding: 24 }}>{children}</main>
      </body>
    </html>
  );
}