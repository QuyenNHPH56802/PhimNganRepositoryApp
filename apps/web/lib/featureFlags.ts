/**
 * Feature flags.
 *
 * - Build-time defaults come from `NEXT_PUBLIC_FLAG_<NAME>` env vars (true/false).
 * - Runtime overrides come from localStorage under `translator.feature_flags`
 *   (a JSON object of `{ flagName: true|false }`) so admins can flip flags
 *   without redeploying.
 * - Admin overrides take precedence over env defaults.
 * - A list of registered flags lives in `KNOWN_FLAGS` so the admin UI can
 *   render them without hand-maintaining a separate registry.
 */
"use client";

import { useEffect, useState } from "react";

export interface FlagSpec {
  /** Stable id used in env, DB, and localStorage. */
  name: string;
  /** Human-readable Vietnamese label. */
  label: string;
  /** Vietnamese description shown in the admin UI. */
  description: string;
  /** Optional category for grouping. */
  group?: "pipeline" | "ui" | "experimental" | "ops";
  /** Default value if no env override and no runtime override. */
  defaultValue: boolean;
}

/**
 * Registry of known flags.
 *
 * To add a new flag: append an entry here, then reference it via
 * `useFlag("name")` or `isFlagEnabled("name")`.
 */
export const KNOWN_FLAGS: FlagSpec[] = [
  {
    name: "WORKFLOW_SUBTITLE_ALIGNMENT_V2",
    label: "Subtitle-Alignment v2",
    description: "Dùng thuật toán căn chỉnh subtitle-thời gian mới (nhanh hơn, ít lỗi timing).",
    group: "pipeline",
    defaultValue: true,
  },
  {
    name: "PIPELINE_VOICE_CLONE",
    label: "Voice Cloning trong pipeline",
    description: "Cho phép bước TTS dùng giọng clone (cần consent cho từng speaker).",
    group: "pipeline",
    defaultValue: false,
  },
  {
    name: "USE_NEW_AUDIO_MIXER",
    label: "Audio mixer mới (Web Audio API)",
    description: "Thử nghiệm giao diện mixer trong trình duyệt — có thể tốn CPU hơn.",
    group: "ui",
    defaultValue: false,
  },
  {
    name: "ENABLE_DIAGNOSTICS_BANNER",
    label: "Diagnostics banner",
    description: "Hiển thị banner cảnh báo khi phát hiện workflow đang chạy chậm bất thường.",
    group: "ops",
    defaultValue: true,
  },
  {
    name: "EXPERIMENTAL_RENDER_PIPELINE",
    label: "Render pipeline thử nghiệm",
    description: "Dùng đường ống render mới (chưa stable — chỉ bật cho test).",
    group: "experimental",
    defaultValue: false,
  },
];

export type FlagName = (typeof KNOWN_FLAGS)[number]["name"];

const STORAGE_KEY = "translator.feature_flags";

function readEnv(name: FlagName): boolean | undefined {
  if (typeof process === "undefined") return undefined;
  const raw = process.env[`NEXT_PUBLIC_FLAG_${name}`];
  if (raw === undefined) return undefined;
  return raw === "true" || raw === "1";
}

function readOverrides(): Partial<Record<FlagName, boolean>> {
  if (typeof window === "undefined") return {};
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return typeof parsed === "object" && parsed !== null
      ? (parsed as Partial<Record<FlagName, boolean>>)
      : {};
  } catch {
    return {};
  }
}

/** Synchronous check (use inside React effects or non-component code). */
export function isFlagEnabled(name: FlagName): boolean {
  const override = readOverrides()[name];
  if (override !== undefined) return override;
  const env = readEnv(name);
  if (env !== undefined) return env;
  return KNOWN_FLAGS.find((f) => f.name === name)?.defaultValue ?? false;
}

/**
 * Persist a runtime override. Pass `undefined` to clear the override for that
 * flag (falls back to env/default).
 */
export function setFlagOverride(name: FlagName, value: boolean | undefined): void {
  if (typeof window === "undefined") return;
  const current = readOverrides();
  const next = { ...current };
  if (value === undefined) {
    delete next[name];
  } else {
    next[name] = value;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  // Notify any subscribed components so they re-render.
  window.dispatchEvent(new CustomEvent("translator:flags-changed", { detail: next }));
}

/** Clear all overrides (back to env + defaults). */
export function clearAllFlagOverrides(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new CustomEvent("translator:flags-changed", { detail: {} }));
}

/**
 * React hook: returns the current value of a flag and a setter for runtime
 * overrides. Re-renders when any flag changes (storage event + custom event).
 */
export function useFlag(name: FlagName): [boolean, (v: boolean | undefined) => void] {
  // Read on every render; cheap because overrides are tiny.
  const value = isFlagEnabled(name);
  const setValue = (v: boolean | undefined) => setFlagOverride(name, v);
  return [value, setValue];
}

/**
 * React hook: returns the full map of all known flags (env + override).
 */
export function useAllFlags(): Record<FlagName, { value: boolean; source: "env" | "override" | "default" }> {
  // Force re-render on storage / custom event.
  const [, force] = useState(0);
  useEffect(() => {
    if (typeof window === "undefined") return;
    const onChange = () => force((x) => x + 1);
    window.addEventListener("storage", onChange);
    window.addEventListener("translator:flags-changed", onChange as EventListener);
    return () => {
      window.removeEventListener("storage", onChange);
      window.removeEventListener("translator:flags-changed", onChange as EventListener);
    };
  }, []);

  const overrides = readOverrides();
  const result = {} as Record<FlagName, { value: boolean; source: "env" | "override" | "default" }>;
  for (const spec of KNOWN_FLAGS) {
    if (overrides[spec.name] !== undefined) {
      result[spec.name] = { value: overrides[spec.name]!, source: "override" };
    } else if (readEnv(spec.name) !== undefined) {
      result[spec.name] = { value: readEnv(spec.name)!, source: "env" };
    } else {
      result[spec.name] = { value: spec.defaultValue, source: "default" };
    }
  }
  return result;
}
