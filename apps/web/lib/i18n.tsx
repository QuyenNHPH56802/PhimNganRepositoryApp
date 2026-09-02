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
  // Lazy init so we read localStorage only on the client (avoids SSR
  // hydration mismatches when the saved locale differs from the default).
  const [locale, setLocaleState] = useState<Locale>(() => {
    if (typeof window === "undefined") return "vi";
    const saved = window.localStorage.getItem("translator.locale");
    return isLocale(saved) ? saved : "vi";
  });

  useEffect(() => {
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
        // Always fall back to English — never to another user-selected locale
        // — so missing keys get a consistent baseline across languages.
        const fb = getByPath(CATALOGS.en, path);
        if (typeof fb === "string") return fb;
        if (process.env.NODE_ENV !== "production" && typeof console !== "undefined") {
          console.warn(`[i18n] Missing key: ${path}`);
        }
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
