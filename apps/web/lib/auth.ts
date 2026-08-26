"use client";

const STORAGE_KEY = "translator_session_token";

export function saveToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, token);
}

export function loadToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(STORAGE_KEY);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(STORAGE_KEY);
}

export interface SessionUser {
  user_id: string;
  email: string;
  provider: string;
}

export async function fetchSessionUser(baseUrl: string): Promise<SessionUser | null> {
  const token = loadToken();
  if (!token) return null;
  const response = await fetch(`${baseUrl}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!response.ok) return null;
  return (await response.json()) as SessionUser;
}

export async function loginStub(
  baseUrl: string,
  email: string,
): Promise<string> {
  const response = await fetch(`${baseUrl}/auth/login/stub`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!response.ok) throw new Error(`login failed: ${response.status}`);
  const payload = (await response.json()) as { token: string };
  saveToken(payload.token);
  return payload.token;
}