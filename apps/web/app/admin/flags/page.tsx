"use client";

import { useState } from "react";
import { Button, Card, StatusDot } from "@/components/ui";
import { theme } from "@/lib/theme";
import { useToast } from "@/lib/toast";
import {
  KNOWN_FLAGS,
  clearAllFlagOverrides,
  setFlagOverride,
  useAllFlags,
  type FlagName,
  type FlagSpec,
} from "@/lib/featureFlags";

const GROUP_LABELS: Record<NonNullable<FlagSpec["group"]>, string> = {
  pipeline: "Pipeline",
  ui: "Giao diện",
  experimental: "Thử nghiệm",
  ops: "Vận hành",
};

const SOURCE_LABELS = {
  env: "Biến môi trường",
  override: "Đã ghi đè (runtime)",
  default: "Mặc định",
} as const;

export default function FeatureFlagsPage() {
  const flags = useAllFlags();
  const toast = useToast();
  const [pendingName, setPendingName] = useState<FlagName | null>(null);

  const grouped = KNOWN_FLAGS.reduce<Record<string, FlagSpec[]>>((acc, spec) => {
    const g = spec.group ?? "other";
    if (!acc[g]) acc[g] = [];
    acc[g].push(spec);
    return acc;
  }, {});

  function handleToggle(spec: FlagSpec, next: boolean) {
    setPendingName(spec.name);
    try {
      setFlagOverride(spec.name, next);
      toast(
        `${spec.label}: ${next ? "đã bật" : "đã tắt"} (${SOURCE_LABELS.override})`,
        "info",
      );
    } catch (err) {
      toast(err instanceof Error ? err.message : String(err), "danger");
    } finally {
      setPendingName(null);
    }
  }

  function handleClearOverride(spec: FlagSpec) {
    setFlagOverride(spec.name, undefined);
    toast(`${spec.label}: đã xoá ghi đè`, "info");
  }

  function handleClearAll() {
    if (typeof window !== "undefined" && !window.confirm("Xoá tất cả ghi đè feature flags?")) return;
    clearAllFlagOverrides();
    toast("Đã xoá tất cả ghi đè", "info");
  }

  const overrideCount = Object.values(flags).filter((f) => f.source === "override").length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 18 }}>
      <header
        style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: 16 }}
      >
        <div>
          <h1 style={{ fontSize: 22, margin: 0 }}>🚩 Feature Flags</h1>
          <p style={{ color: theme.textMuted, fontSize: 13, margin: "4px 0 0", maxWidth: 640 }}>
            Bật/tắt tính năng runtime không cần redeploy. Thay đổi được lưu vào localStorage
            của admin hiện tại và ưu tiên cao hơn biến môi trường build-time.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <span
            style={{
              alignSelf: "center",
              fontSize: 11,
              color: theme.textMuted,
              padding: "4px 10px",
              background: theme.bgElevated,
              borderRadius: 4,
            }}
          >
            {overrideCount > 0
              ? `${overrideCount} ghi đè đang hoạt động`
              : "Không có ghi đè"}
          </span>
          {overrideCount > 0 && (
            <Button size="sm" variant="ghost" onClick={handleClearAll}>
              🗑 Xoá tất cả ghi đè
            </Button>
          )}
        </div>
      </header>

      {Object.entries(grouped).map(([group, specs]) => (
        <section key={group}>
          <h2
            style={{
              fontSize: 14,
              fontWeight: 700,
              textTransform: "uppercase",
              letterSpacing: 0.6,
              color: theme.textMuted,
              margin: "8px 0 10px",
            }}
          >
            {GROUP_LABELS[group as NonNullable<FlagSpec["group"]>] ?? group}
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(360px, 1fr))", gap: 12 }}>
            {specs.map((spec) => {
              const f = flags[spec.name];
              const isPending = pendingName === spec.name;
              return (
                <Card key={spec.name} padded>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 8 }}>
                      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                        <StatusDot
                          status={f.source === "override" ? "editing" : f.value ? "completed" : "pending"}
                        />
                        <strong style={{ fontSize: 13 }}>{spec.label}</strong>
                      </div>
                      <label
                        style={{
                          position: "relative",
                          display: "inline-block",
                          width: 40,
                          height: 22,
                          cursor: isPending ? "wait" : "pointer",
                          opacity: isPending ? 0.6 : 1,
                        }}
                      >
                        <input
                          type="checkbox"
                          checked={f.value}
                          onChange={(e) => handleToggle(spec, e.target.checked)}
                          disabled={isPending}
                          aria-label={`${spec.label} toggle`}
                          style={{ position: "absolute", opacity: 0, pointerEvents: "none" }}
                        />
                        <span
                          style={{
                            position: "absolute",
                            inset: 0,
                            background: f.value ? theme.accentStrong : theme.bgElevated,
                            border: `1px solid ${theme.border}`,
                            borderRadius: 999,
                            transition: "background 150ms ease",
                          }}
                        />
                        <span
                          style={{
                            position: "absolute",
                            top: 2,
                            left: f.value ? 20 : 2,
                            width: 16,
                            height: 16,
                            background: "#fff",
                            borderRadius: 999,
                            transition: "left 150ms ease",
                          }}
                        />
                      </label>
                    </div>
                    <p style={{ margin: 0, fontSize: 12, color: theme.textMuted }}>{spec.description}</p>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        fontSize: 11,
                        color: theme.textDim,
                      }}
                    >
                      <span>
                        Nguồn: <strong style={{ color: theme.textMuted }}>{SOURCE_LABELS[f.source]}</strong>
                      </span>
                      {f.source === "override" && (
                        <button
                          onClick={() => handleClearOverride(spec)}
                          style={{
                            background: "transparent",
                            border: "none",
                            color: theme.accent,
                            fontSize: 11,
                            cursor: "pointer",
                            textDecoration: "underline",
                            padding: 0,
                          }}
                        >
                          Xoá ghi đè
                        </button>
                      )}
                    </div>
                    <code
                      style={{
                        fontSize: 10,
                        background: theme.bgElevated,
                        padding: "2px 6px",
                        borderRadius: 3,
                        color: theme.textDim,
                        alignSelf: "flex-start",
                      }}
                    >
                      NEXT_PUBLIC_FLAG_{spec.name}
                    </code>
                  </div>
                </Card>
              );
            })}
          </div>
        </section>
      ))}

      <Card title="Cách hoạt động" padded>
        <ol style={{ margin: 0, paddingLeft: 20, fontSize: 13, color: theme.textMuted, display: "flex", flexDirection: "column", gap: 6 }}>
          <li>
            Mỗi flag có 3 nguồn giá trị, xếp theo thứ tự ưu tiên từ cao xuống thấp:
            <ol style={{ marginTop: 4 }}>
              <li><strong style={{ color: theme.text }}>Ghi đè runtime</strong> — lưu ở <code>localStorage["translator.feature_flags"]</code></li>
              <li><strong style={{ color: theme.text }}>Biến môi trường</strong> — <code>NEXT_PUBLIC_FLAG_&lt;NAME&gt;</code> trong <code>.env</code></li>
              <li><strong style={{ color: theme.text }}>Mặc định</strong> — khai báo trong <code>lib/featureFlags.ts</code></li>
            </ol>
          </li>
          <li>Toggle chỉ có hiệu lực cho admin hiện tại trên trình duyệt này (cần reload trang).</li>
          <li>
            Để thêm flag mới: thêm một entry vào mảng <code>KNOWN_FLAGS</code> trong
            <code> lib/featureFlags.ts</code>, sau đó tham chiếu qua <code>useFlag("NAME")</code> trong component.
          </li>
        </ol>
      </Card>
    </div>
  );
}
