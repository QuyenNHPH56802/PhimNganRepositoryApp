export const theme = {
  bg: "#0b1220",
  bgElevated: "#0f172a",
  bgPanel: "#111c33",
  border: "#1f2a44",
  borderStrong: "#2c3a5a",
  text: "#e2e8f0",
  textMuted: "#94a3b8",
  textDim: "#64748b",
  accent: "#7dd3fc",
  accentStrong: "#0ea5e9",
  success: "#22c55e",
  warn: "#f59e0b",
  danger: "#ef4444",
  speaker1: "#60a5fa",
  speaker2: "#f472b6",
  speaker3: "#34d399",
  speaker4: "#fbbf24",
  fontSans: "system-ui, -apple-system, sans-serif",
} as const;

export function speakerColor(index: number): string {
  const palette: string[] = [theme.speaker1, theme.speaker2, theme.speaker3, theme.speaker4, "#a78bfa", "#fb7185"];
  return palette[index % palette.length] ?? theme.speaker1;
}
