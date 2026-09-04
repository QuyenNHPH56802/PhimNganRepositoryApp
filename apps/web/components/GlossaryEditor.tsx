"use client";

import { useEffect, useState } from "react";
import { Button, Card, EmptyState, Input, SkeletonPanel, StatusDot, useToast } from "@/components/ui";
import { theme } from "@/lib/theme";
import {
  activateGlossary,
  addTerm,
  createGlossary,
  deleteGlossary,
  deleteTerm,
  listGlossaries,
  type Glossary,
  type GlossaryTermInput,
} from "@/lib/glossary";

/**
 * Inline glossary editor for a project.
 *
 * Renders the list of glossary versions with the active one highlighted, an
 * inline editor for adding terms, and bulk delete. Designed to be mounted
 * from both the project workspace sidebar and the global settings page.
 */
export function GlossaryEditor({ projectId }: { projectId: string }) {
  const [glossaries, setGlossaries] = useState<Glossary[] | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { toast } = useToast();

  // Add-term form state.
  const [newZh, setNewZh] = useState("");
  const [newVi, setNewVi] = useState("");
  const [newCategory, setNewCategory] = useState("");
  const [newPriority, setNewPriority] = useState(0);

  // New-glossary form state.
  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

  async function refresh() {
    setLoading(true);
    try {
      const list = await listGlossaries(projectId);
      setGlossaries(list);
      const active = list.find((g) => g.is_active);
      if (active) setSelectedId(active.id);
      else if (list[0]) setSelectedId(list[0].id);
      else setSelectedId(null);
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  async function handleAddTerm() {
    if (!selectedId || !newZh.trim() || !newVi.trim()) {
      toast("Cần nhập cả thuật ngữ Trung và Việt", "warn");
      return;
    }
    setSaving(true);
    try {
      const term: GlossaryTermInput = {
        chinese: newZh.trim(),
        vietnamese: newVi.trim(),
        category: newCategory.trim() || null,
        priority: newPriority,
      };
      const updated = await addTerm(projectId, selectedId, term);
      setGlossaries((prev) => prev?.map((g) => (g.id === updated.id ? updated : g)) ?? null);
      setNewZh("");
      setNewVi("");
      setNewCategory("");
      setNewPriority(0);
      toast("Đã thêm thuật ngữ", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteTerm(termId: string) {
    if (!selectedId) return;
    if (typeof window !== "undefined" && !window.confirm("Xoá thuật ngữ này?")) return;
    setSaving(true);
    try {
      await deleteTerm(projectId, selectedId, termId);
      const list = await listGlossaries(projectId);
      setGlossaries(list);
      toast("Đã xoá thuật ngữ", "info");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setSaving(false);
    }
  }

  async function handleCreate() {
    if (!newName.trim()) {
      toast("Cần đặt tên glossary", "warn");
      return;
    }
    setSaving(true);
    try {
      const g = await createGlossary(projectId, { name: newName.trim(), terms: [], activate: true });
      setNewName("");
      setCreating(false);
      const list = await listGlossaries(projectId);
      setGlossaries(list);
      setSelectedId(g.id);
      toast(`Đã tạo glossary "${g.name}"`, "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setSaving(false);
    }
  }

  async function handleActivate(id: string) {
    setSaving(true);
    try {
      await activateGlossary(projectId, id);
      const list = await listGlossaries(projectId);
      setGlossaries(list);
      setSelectedId(id);
      toast("Đã kích hoạt glossary", "success");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteGlossary(id: string) {
    if (typeof window !== "undefined" && !window.confirm("Xoá vĩnh viễn glossary này?")) return;
    setSaving(true);
    try {
      await deleteGlossary(projectId, id);
      const list = await listGlossaries(projectId);
      setGlossaries(list);
      const active = list.find((g) => g.is_active);
      setSelectedId(active?.id ?? list[0]?.id ?? null);
      toast("Đã xoá glossary", "info");
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setSaving(false);
    }
  }

  if (loading && glossaries === null) {
    return <SkeletonPanel title="Glossary" rows={3} />;
  }

  if (glossaries === null) return null;

  if (glossaries.length === 0) {
    return (
      <Card title="Glossary" padded>
        <EmptyState
          title="Chưa có glossary"
          description="Glossary là bảng thuật ngữ Trung ↔ Việt mà bạn muốn dịch nhất quán trong mọi segment (tên riêng, địa danh, thuật ngữ ngành…)."
          action={
            <Button variant="primary" onClick={() => setCreating(true)} disabled={creating}>
              + Tạo glossary đầu tiên
            </Button>
          }
        />
        {creating && (
          <CreateForm
            newName={newName}
            setNewName={setNewName}
            saving={saving}
            onCancel={() => setCreating(false)}
            onConfirm={handleCreate}
          />
        )}
      </Card>
    );
  }

  const selected = glossaries.find((g) => g.id === selectedId);

  return (
    <Card
      title={`Glossary (${glossaries.length} phiên bản)`}
      padded={false}
      action={
        <Button size="sm" variant="ghost" onClick={() => setCreating((v) => !v)} disabled={saving}>
          {creating ? "✕ Huỷ" : "+ Tạo mới"}
        </Button>
      }
    >
      {creating && (
        <CreateForm
          newName={newName}
          setNewName={setNewName}
          saving={saving}
          onCancel={() => setCreating(false)}
          onConfirm={handleCreate}
        />
      )}

      <div
        role="tablist"
        aria-label="Glossary versions"
        style={{
          display: "flex",
          gap: 4,
          padding: "8px 12px",
          borderBottom: `1px solid ${theme.border}`,
          background: "#0d172e",
          overflowX: "auto",
        }}
      >
        {glossaries.map((g) => (
          <button
            key={g.id}
            role="tab"
            aria-selected={selectedId === g.id}
            onClick={() => setSelectedId(g.id)}
            style={{
              padding: "4px 10px",
              borderRadius: 4,
              border: `1px solid ${selectedId === g.id ? theme.accentStrong : theme.border}`,
              background: selectedId === g.id ? "rgba(125,211,252,0.1)" : "transparent",
              color: selectedId === g.id ? theme.text : theme.textMuted,
              fontSize: 12,
              fontWeight: 600,
              cursor: "pointer",
              whiteSpace: "nowrap",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <StatusDot status={g.is_active ? "completed" : "pending"} />
            v{g.version} · {g.name}
            <span style={{ color: theme.textDim, fontWeight: 400 }}>({g.terms.length})</span>
          </button>
        ))}
      </div>

      {selected && (
        <div style={{ padding: 14, display: "flex", flexDirection: "column", gap: 12 }}>
          <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
            {selected.is_active ? (
              <span
                style={{
                  fontSize: 11,
                  padding: "2px 8px",
                  borderRadius: 4,
                  background: "rgba(34,197,94,0.15)",
                  color: theme.success,
                  fontWeight: 700,
                }}
              >
                ✓ Đang được dùng
              </span>
            ) : (
              <Button size="sm" variant="primary" onClick={() => handleActivate(selected.id)} disabled={saving}>
                Kích hoạt phiên bản này
              </Button>
            )}
            <Button size="sm" variant="danger" onClick={() => handleDeleteGlossary(selected.id)} disabled={saving}>
              Xoá phiên bản
            </Button>
            <span style={{ fontSize: 11, color: theme.textMuted, marginLeft: "auto" }}>
              Tạo: {new Date(selected.created_at).toLocaleString()}
            </span>
          </div>

          {/* Add-term form */}
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "1fr 1fr 1fr 90px auto",
              gap: 8,
              alignItems: "end",
              padding: 10,
              background: theme.bgElevated,
              border: `1px dashed ${theme.border}`,
              borderRadius: 6,
            }}
          >
            <Field label="中文">
              <Input value={newZh} onChange={(e) => setNewZh(e.target.value)} placeholder="例如：机器学习" />
            </Field>
            <Field label="Tiếng Việt">
              <Input value={newVi} onChange={(e) => setNewVi(e.target.value)} placeholder="Học máy" />
            </Field>
            <Field label="Nhóm">
              <Input value={newCategory} onChange={(e) => setNewCategory(e.target.value)} placeholder="(tuỳ chọn)" />
            </Field>
            <Field label="Ưu tiên">
              <Input
                type="number"
                value={newPriority}
                onChange={(e) => setNewPriority(parseInt(e.target.value || "0", 10))}
              />
            </Field>
            <Button variant="primary" onClick={handleAddTerm} disabled={saving || !selected.is_active}>
              {saving ? "…" : "+ Thêm"}
            </Button>
          </div>
          {!selected.is_active && (
            <p style={{ fontSize: 11, color: theme.textDim, margin: 0 }}>
              ⓘ Chỉ phiên bản đang kích hoạt mới nhận thuật ngữ mới.
            </p>
          )}

          {/* Term list */}
          {selected.terms.length === 0 ? (
            <EmptyState title="Chưa có thuật ngữ" description="Dùng form bên trên để thêm." />
          ) : (
            <div role="table" aria-label="Glossary terms">
              <div
                role="row"
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr 1fr 70px 70px",
                  gap: 8,
                  padding: "8px 10px",
                  borderBottom: `1px solid ${theme.border}`,
                  fontSize: 11,
                  fontWeight: 700,
                  color: theme.textMuted,
                  textTransform: "uppercase",
                }}
              >
                <span>中文</span>
                <span>Tiếng Việt</span>
                <span>Nhóm</span>
                <span>Ưu tiên</span>
                <span></span>
              </div>
              {selected.terms.map((t) => (
                <div
                  role="row"
                  key={t.id}
                  style={{
                    display: "grid",
                    gridTemplateColumns: "1fr 1fr 1fr 70px 70px",
                    gap: 8,
                    padding: "8px 10px",
                    borderBottom: `1px solid ${theme.border}`,
                    fontSize: 13,
                    alignItems: "center",
                  }}
                >
                  <span style={{ fontFamily: "ui-monospace, monospace" }}>{t.chinese}</span>
                  <span>{t.vietnamese}</span>
                  <span style={{ color: theme.textMuted, fontSize: 12 }}>{t.category ?? "—"}</span>
                  <span style={{ color: theme.textMuted, fontSize: 12 }}>{t.priority}</span>
                  <button
                    onClick={() => handleDeleteTerm(t.id)}
                    disabled={saving}
                    aria-label={`Xoá thuật ngữ ${t.chinese}`}
                    style={{
                      background: "transparent",
                      border: `1px solid ${theme.border}`,
                      color: theme.danger,
                      padding: "2px 8px",
                      borderRadius: 4,
                      cursor: "pointer",
                      fontSize: 11,
                    }}
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}

function CreateForm({
  newName,
  setNewName,
  saving,
  onCancel,
  onConfirm,
}: {
  newName: string;
  setNewName: (v: string) => void;
  saving: boolean;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  return (
    <div
      style={{
        padding: 10,
        display: "flex",
        gap: 8,
        alignItems: "end",
        borderBottom: `1px solid ${theme.border}`,
        background: theme.bgElevated,
      }}
    >
      <Field label="Tên glossary">
        <Input
          value={newName}
          onChange={(e) => setNewName(e.target.value)}
          placeholder="VD: Tên riêng phim truyền hình"
          autoFocus
          style={{ minWidth: 320 }}
        />
      </Field>
      <Button variant="primary" onClick={onConfirm} disabled={saving}>
        {saving ? "…" : "Tạo & kích hoạt"}
      </Button>
      <Button variant="ghost" onClick={onCancel}>
        Huỷ
      </Button>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 10, color: theme.textMuted, fontWeight: 600 }}>{label}</span>
      {children}
    </label>
  );
}
