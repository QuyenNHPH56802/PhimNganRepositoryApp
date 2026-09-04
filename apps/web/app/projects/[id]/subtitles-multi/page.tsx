"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Button, Card, Modal, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";
import {
  generateMultiSubtitles,
  listSubtitleTracks,
  listSupportedLanguages,
  type LanguageTrack,
  type SubtitleLanguage,
} from "@/lib/multiSubtitles";

const STATIC_LANGS: SubtitleLanguage[] = [
  { code: "vi", label: "Tiếng Việt", is_default: true },
  { code: "en", label: "English", is_default: false },
  { code: "ja", label: "日本語", is_default: false },
  { code: "ko", label: "한국어", is_default: false },
  { code: "fr", label: "Français", is_default: false },
  { code: "es", label: "Español", is_default: false },
];

export default function MultiLanguageSubtitlesPage() {
  const params = useParams<{ id: string }>();
  const projectId = params.id;
  const { toast } = useToast();

  const [languages, setLanguages] = useState<SubtitleLanguage[]>(STATIC_LANGS);
  const [tracks, setTracks] = useState<LanguageTrack[]>([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedLangs, setSelectedLangs] = useState<string[]>(["vi"]);
  const [cpsLimit, setCpsLimit] = useState(17);
  const [showGen, setShowGen] = useState(false);
  const [previewLang, setPreviewLang] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const t = await listSubtitleTracks(projectId);
      setTracks(t);
      const ls = await listSupportedLanguages().catch(() => STATIC_LANGS);
      if (Array.isArray(ls) && ls.length > 0) setLanguages(ls);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setLoading(false);
    }
  }, [projectId, toast]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleGenerate() {
    if (selectedLangs.length === 0) {
      toast("Chọn ít nhất 1 ngôn ngữ", "warn");
      return;
    }
    setGenerating(true);
    try {
      const result = await generateMultiSubtitles(projectId, {
        target_languages: selectedLangs,
        cps_limit: cpsLimit,
      });
      toast(`Đã tạo subtitle cho ${result.languages.length} ngôn ngữ`, "success");
      setShowGen(false);
      await refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <header
        style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}
      >
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>🌐 Phụ đề đa ngôn ngữ</h1>
          <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0", maxWidth: 640 }}>
            Tạo phụ đề tiếng Việt + nhiều ngôn ngữ khác (en, ja, ko, fr, es) cùng lúc.
            Mỗi ngôn ngữ có track riêng, hiển thị được cùng lúc trên video.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Link href={`/projects/${projectId}/workspace`} style={{ textDecoration: "none" }}>
            <Button variant="ghost">← Workspace</Button>
          </Link>
          <Button variant="primary" onClick={() => setShowGen(true)} disabled={loading}>
            + Tạo track mới
          </Button>
        </div>
      </header>

      {loading && tracks.length === 0 && (
        <div style={{ color: theme.textMuted, fontSize: 13, padding: 16 }}>
          Đang tải tracks…
        </div>
      )}

      {!loading && tracks.length === 0 && (
        <Card padded>
          <p style={{ color: theme.textMuted, fontSize: 13, margin: 0 }}>
            Chưa có subtitle track nào cho project này. Nhấn <strong>Tạo track mới</strong> để bắt đầu.
          </p>
        </Card>
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 14 }}>
        {tracks.map((t) => (
          <Card
            key={t.track_id ?? t.language_code}
            title={`${t.language_label} (${t.language_code})`}
            padded={false}
            action={
              <Button size="sm" variant="ghost" onClick={() => setPreviewLang(t.language_code)}>
                Xem
              </Button>
            }
          >
            <div style={{ padding: 14 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <StatusDot status={t.segment_count > 0 ? "completed" : "pending"} />
                <strong style={{ fontSize: 14 }}>{t.segment_count} segments</strong>
              </div>
              {t.segment_count > 0 && (
                <>
                  <p
                    style={{
                      fontSize: 12,
                      color: theme.textMuted,
                      margin: "0 0 8px",
                      lineHeight: 1.5,
                    }}
                  >
                    {t.segments.slice(0, 3).map((s) => s.text).join(" · ")}
                    {t.segments.length > 3 && "…"}
                  </p>
                  <div style={{ fontSize: 11, color: theme.textDim }}>
                    ID: {t.track_id?.slice(0, 8) ?? "—"}
                  </div>
                </>
              )}
              {t.segment_count === 0 && (
                <p style={{ fontSize: 12, color: theme.textDim, margin: 0 }}>
                  Track trống — tạo lại để điền segments.
                </p>
              )}
            </div>
          </Card>
        ))}
      </div>

      {/* Generate modal */}
      <Modal
        open={showGen}
        onClose={() => !generating && setShowGen(false)}
        title="Tạo subtitle cho nhiều ngôn ngữ"
        width={460}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <div>
            <p style={{ margin: "0 0 8px", fontSize: 12, fontWeight: 600 }}>
              Chọn ngôn ngữ đích *
            </p>
            <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              {languages.map((lang) => (
                <label
                  key={lang.code}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 10,
                    padding: "6px 10px",
                    border: `1px solid ${theme.border}`,
                    borderRadius: 4,
                    cursor: "pointer",
                    background: selectedLangs.includes(lang.code) ? "rgba(125,211,252,0.08)" : "transparent",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={selectedLangs.includes(lang.code)}
                    onChange={(e) => {
                      setSelectedLangs((prev) =>
                        e.target.checked ? [...prev, lang.code] : prev.filter((c) => c !== lang.code),
                      );
                    }}
                    disabled={generating}
                  />
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{lang.label}</span>
                  <span style={{ fontSize: 11, color: theme.textDim, marginLeft: "auto" }}>
                    ({lang.code})
                  </span>
                  {lang.is_default && (
                    <span
                      style={{
                        fontSize: 10,
                        color: theme.success,
                        background: "rgba(34,197,94,0.15)",
                        padding: "1px 6px",
                        borderRadius: 3,
                        fontWeight: 700,
                      }}
                    >
                      mặc định
                    </span>
                  )}
                </label>
              ))}
            </div>
          </div>

          <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 12, fontWeight: 600 }}>Giới hạn CPS (ký tự / giây)</span>
            <input
              type="number"
              min={5}
              max={50}
              step={1}
              value={cpsLimit}
              onChange={(e) => setCpsLimit(parseFloat(e.target.value || "17"))}
              disabled={generating}
              style={{
                background: theme.bgPanel,
                border: `1px solid ${theme.border}`,
                color: theme.text,
                padding: "6px 10px",
                borderRadius: 4,
                fontSize: 13,
              }}
            />
            <span style={{ fontSize: 11, color: theme.textMuted }}>
              Subtitle sẽ tự tách dòng khi vượt quá CPS. Mặc định 17 cps — phù hợp tiếng Việt.
            </span>
          </label>

          <div
            style={{
              padding: 10,
              background: theme.bgElevated,
              borderRadius: 4,
              fontSize: 11,
              color: theme.textMuted,
            }}
          >
            ⓘ Ngôn ngữ không phải VI sẽ được dịch tự động từ bản dịch tiếng Việt hiện có.
            Tốn 1 lượt translation cho mỗi segment của mỗi ngôn ngữ.
          </div>

          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
            <Button variant="ghost" onClick={() => setShowGen(false)} disabled={generating}>
              Huỷ
            </Button>
            <Button variant="primary" onClick={handleGenerate} disabled={generating}>
              {generating ? "⏳ Đang tạo…" : `Tạo ${selectedLangs.length} track`}
            </Button>
          </div>
        </div>
      </Modal>

      {/* Preview modal */}
      <Modal
        open={previewLang !== null}
        onClose={() => setPreviewLang(null)}
        title={`Preview subtitle: ${previewLang}`}
        width={600}
      >
        {previewLang && tracks.find((t) => t.language_code === previewLang)?.segments ? (
          <div style={{ display: "flex", flexDirection: "column", gap: 4, maxHeight: 480, overflowY: "auto" }}>
            {tracks
              .find((t) => t.language_code === previewLang)!
              .segments.map((s, i) => (
                <div
                  key={s.id || i}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "60px 100px 1fr",
                    gap: 8,
                    padding: "4px 0",
                    fontSize: 12,
                    borderBottom: `1px solid ${theme.border}`,
                    alignItems: "center",
                  }}
                >
                  <span style={{ color: theme.textDim, fontFamily: "ui-monospace" }}>#{s.idx}</span>
                  <span style={{ color: theme.textMuted, fontFamily: "ui-monospace" }}>
                    {(s.start_ms / 1000).toFixed(2)}s
                  </span>
                  <span>{s.text}</span>
                </div>
              ))}
          </div>
        ) : (
          <p style={{ color: theme.textMuted }}>Không có segment.</p>
        )}
      </Modal>
    </div>
  );
}
