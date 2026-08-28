"use client";

import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

import vi from "@/messages/vi.json";
import en from "@/messages/en.json";
import zh from "@/messages/zh.json";
import ja from "@/messages/ja.json";
import ko from "@/messages/ko.json";
import fr from "@/messages/fr.json";
import de from "@/messages/de.json";
import es from "@/messages/es.json";
import pt from "@/messages/pt.json";
import th from "@/messages/th.json";

export const SUPPORTED_LOCALES = ["vi", "en", "zh", "ja", "ko", "fr", "de", "es", "pt", "th"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

const CATALOGS: Record<Locale, Record<string, unknown>> = {
  vi,
  en,
  zh,
  ja,
  ko,
  fr,
  de,
  es,
  pt,
  th,
};

export const LOCALE_LABELS: Record<Locale, string> = {
  vi: "Tiếng Việt",
  en: "English",
  zh: "中文",
  ja: "日本語",
  ko: "한국어",
  fr: "Français",
  de: "Deutsch",
  es: "Español",
  pt: "Português",
  th: "ไทย",
};

interface I18nContextValue {
  locale: Locale;
  setLocale: (l: Locale) => void;
  t: (path: string, fallback?: string) => string;
}

const I18nContext = createContext<I18nContextValue | null>(null);

function getByPath(obj: unknown, path: string): unknown {
  return path.split(".").reduce<unknown>((acc, key) => {
    if (acc && typeof acc === "object" && key in (acc as Record<string, unknown>)) {
      return (acc as Record<string, unknown>)[key];
    }
    return undefined;
  }, obj);
}

function isLocale(value: string | null | undefined): value is Locale {
  return !!value && (SUPPORTED_LOCALES as readonly string[]).includes(value);
}

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("vi");

  useEffect(() => {
    const saved = typeof window !== "undefined" ? window.localStorage.getItem("translator.locale") : null;
    if (isLocale(saved)) setLocaleState(saved);
    document.documentElement.lang = locale;
  }, [locale]);

  const value = useMemo<I18nContextValue>(
    () => ({
      locale,
      setLocale: (l: Locale) => {
        setLocaleState(l);
        if (typeof window !== "undefined") {
          window.localStorage.setItem("translator.locale", l);
          document.documentElement.lang = l;
        }
      },
      t: (path, fallback) => {
        const primary = getByPath(CATALOGS[locale], path);
        if (typeof primary === "string") return primary;
        const fallbackLocale: Locale = locale === "vi" ? "en" : "vi";
        const fb = getByPath(CATALOGS[fallbackLocale], path);
        if (typeof fb === "string") return fb;
        return fallback ?? path;
      },
    }),
    [locale],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useT() {
  const ctx = useContext(I18nContext);
  if (!ctx) throw new Error("useT must be used inside <I18nProvider>");
  return ctx;
}
