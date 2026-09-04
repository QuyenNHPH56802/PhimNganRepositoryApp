"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Button, Card, EmptyState, Input, Modal } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";
import {
  applyTemplate,
  createTemplate,
  deleteTemplate,
  duplicateTemplate,
  listTemplates,
  type ProjectTemplate,
  type ProjectTemplateInput,
} from "@/lib/templates";

const QUALITY_MODES = ["fast", "balanced", "high"] as const;
const LANGUAGE_PROFILES = [
  { value: "zh-vi", label: "Chinese → Vietnamese" },
  { value: "zh-en", label: "Chinese → English" },
  { value: "en-vi", label: "English → Vietnamese" },
];

const EMPTY_FORM: ProjectTemplateInput = {
  name: "",
  description: null,
  quality_mode: "balanced",
  language_profile: "zh-vi",
  source_language: "zh",
  target_language: "vi",
  tts_provider_id: null,
  translate_provider_id: null,
  glossary_id: null,
  config: {},
};

export default function TemplatesPage() {
  const { toast } = useToast();
  const [templates, setTemplates] = useState<ProjectTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<ProjectTemplateInput>(EMPTY_FORM);
  const [applyingId, setApplyingId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const list = await listTemplates();
      setTemplates(Array.isArray(list) ? list : []);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setLoading(false);
    }
  }, [toast]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function handleCreate() {
    if (!form.name.trim()) {
      toast("Cần đặt tên template", "warn");
      return;
    }
    try {
      const t = await createTemplate({
        ...form,
        name: form.name.trim(),
        description: form.description?.trim() || null,
      });
      toast(`Đã tạo template "${t.name}"`, "success");
      setForm(EMPTY_FORM);
      setShowForm(false);
      await refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  async function handleDelete(t: ProjectTemplate) {
    if (!window.confirm(`Xoá template "${t.name}"?`)) return;
    try {
      await deleteTemplate(t.id);
      toast("Đã xoá", "info");
      await refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  async function handleDuplicate(t: ProjectTemplate) {
    try {
      const copy = await duplicateTemplate(t.id);
      toast(`Đã duplicate: ${copy.name}`, "success");
      await refresh();
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    }
  }

  async function handleApply(t: ProjectTemplate) {
    setApplyingId(t.id);
    try {
      const result = await applyTemplate(t.id);
      toast(
        `Template "${t.name}" đã apply (${result.use_count} lần dùng) — copy payload để tạo project`,
        "success",
      );
      // Copy the payload to clipboard for convenience.
      if (typeof navigator !== "undefined" && navigator.clipboard) {
        await navigator.clipboard.writeText(JSON.stringify(result.payload, null, 2));
        toast("Payload đã được copy vào clipboard", "info");
      }
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setApplyingId(null);
    }
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <header
        style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}
      >
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>📑 Project Templates</h1>
          <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0", maxWidth: 640 }}>
            Lưu cấu hình project (chất lượng, ngôn ngữ, providers, glossary) để dùng lại
            cho các video cùng series — không phải cấu hình lại từ đầu.
          </p>
        </div>
        <Button variant="primary" onClick={() => setShowForm(true)}>
          + Tạo template
        </Button>
      </header>

      {loading && templates.length === 0 && (
        <div style={{ color: theme.textMuted, fontSize: 13, padding: 16 }}>Đang tải…</div>
      )}

      {!loading && templates.length === 0 && (
        <EmptyState
          title="Chưa có template"
          description="Tạo template đầu tiên để áp dụng nhanh cho project mới."
          action={
            <Button variant="primary" onClick={() => setShowForm(true)}>
              + Tạo template đầu tiên
            </Button>
          }
        />
      )}

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))", gap: 14 }}>
        {templates.map((t) => (
          <Card key={t.id} title={t.name} padded>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {t.description && (
                <p style={{ fontSize: 12, color: theme.textMuted, margin: 0 }}>{t.description}</p>
              )}

              <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
                <Chip label={`Q: ${t.quality_mode}`} />
                <Chip label={t.language_profile} />
                {t.tts_provider_id && <Chip label={`TTS: ${t.tts_provider_id}`} />}
                {t.translate_provider_id && (
                  <Chip label={`Translate: ${t.translate_provider_id}`} />
                )}
              </div>

              <div style={{ fontSize: 11, color: theme.textDim, marginTop: "auto" }}>
                Tạo: {new Date(t.created_at).toLocaleDateString()} &nbsp;·&nbsp;
                Đã dùng: {t.use_count} lần
              </div>

              <div style={{ display: "flex", gap: 6, marginTop: 4 }}>
                <Button
                  size="sm"
                  variant="primary"
                  onClick={() => handleApply(t)}
                  disabled={applyingId === t.id}
                >
                  {applyingId === t.id ? "…" : "▶ Apply"}
                </Button>
                <Button size="sm" variant="ghost" onClick={() => handleDuplicate(t)}>
                  Duplicate
                </Button>
                <Button size="sm" variant="danger" onClick={() => handleDelete(t)}>
                  Xoá
                </Button>
              </div>
            </div>
          </Card>
        ))}
      </div>

      {/* Create template modal */}
      <Modal
        open={showForm}
        onClose={() => setShowForm(false)}
        title="Tạo Project Template"
        width={500}
      >
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <Field label="Tên *">
            <Input
              value={form.name}
              onChange={(e) => setForm((p) => ({ ...p, name: e.target.value }))}
              placeholder="VD: Phim ngắn — chuẩn hoá"
              autoFocus
            />
          </Field>
          <Field label="Mô tả">
            <Input
              value={form.description ?? ""}
              onChange={(e) => setForm((p) => ({ ...p, description: e.target.value || null }))}
              placeholder="(tuỳ chọn)"
            />
          </Field>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Field label="Quality mode">
              <select
                value={form.quality_mode}
                onChange={(e) => setForm((p) => ({ ...p, quality_mode: e.target.value }))}
                style={selectStyle}
              >
                {QUALITY_MODES.map((q) => (
                  <option key={q} value={q}>
                    {q}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Language profile">
              <select
                value={form.language_profile}
                onChange={(e) => setForm((p) => ({ ...p, language_profile: e.target.value }))}
                style={selectStyle}
              >
                {LANGUAGE_PROFILES.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
            <Field label="TTS provider">
              <Input
                value={form.tts_provider_id ?? ""}
                onChange={(e) => setForm((p) => ({ ...p, tts_provider_id: e.target.value || null }))}
                placeholder="azure / google / …"
              />
            </Field>
            <Field label="Translate provider">
              <Input
                value={form.translate_provider_id ?? ""}
                onChange={(e) =>
                  setForm((p) => ({ ...p, translate_provider_id: e.target.value || null }))
                }
                placeholder="openai / gemini / …"
              />
            </Field>
          </div>
          <div style={{ display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 8 }}>
            <Button variant="ghost" onClick={() => setShowForm(false)}>
              Huỷ
            </Button>
            <Button variant="primary" onClick={handleCreate}>
              Tạo
            </Button>
          </div>
        </div>
      </Modal>

      <Card title="Cách dùng" padded>
        <ol style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: theme.textMuted, display: "flex", flexDirection: "column", gap: 4 }}>
          <li>
            Tạo template với cấu hình hay dùng (quality mode + language profile + providers).
          </li>
          <li>
            Trên trang tạo project mới, nhấn <strong style={{ color: theme.text }}>Apply</strong>{" "}
            — payload JSON sẽ được copy vào clipboard, paste vào form tạo project.
          </li>
          <li>
            Mỗi lần apply đều tăng <em>use_count</em> — biết được template nào được dùng nhiều nhất.
          </li>
        </ol>
      </Card>
    </div>
  );
}

function Chip({ label }: { label: string }) {
  return (
    <span
      style={{
        fontSize: 10,
        padding: "2px 6px",
        borderRadius: 3,
        background: theme.bgElevated,
        border: `1px solid ${theme.border}`,
        color: theme.textMuted,
        fontFamily: "ui-monospace, monospace",
      }}
    >
      {label}
    </span>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 11, color: theme.textMuted, fontWeight: 600 }}>{label}</span>
      {children}
    </label>
  );
}

const selectStyle: React.CSSProperties = {
  background: theme.bgPanel,
  border: `1px solid ${theme.border}`,
  color: theme.text,
  padding: "6px 10px",
  borderRadius: 4,
  fontSize: 13,
};
