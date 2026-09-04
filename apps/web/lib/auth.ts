// Single-user mode: every request is implicitly authenticated as the
// provisioned owner. There is no login flow, so these helpers are kept for
// backward compatibility (e.g. a future multi-user setup) but in practice
// the Authorization header is never attached.
//
// All API calls in `lib/api.ts` and every `app/api/*` route handler guard
// `if (token)`, which is always false in single-user mode — so no
// `Authorization: Bearer null` header ever leaves the client.

const TOKEN_KEY = "translator_session_token";

export function saveToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function loadToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function clearToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
}

// Server-side helper: in single-user mode the backend resolves the owner
// automatically when no Authorization header is sent. Route handlers should
// rely on that, and only forward `Authorization` when a real token exists
// (e.g. once a multi-user flow ships).
export function hasToken(): boolean {
  const t = loadToken();
  return t !== null && t.length > 0;
}
