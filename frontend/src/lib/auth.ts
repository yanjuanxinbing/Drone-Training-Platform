// Client-side auth helpers. Uses localStorage for the JWT.

const TOKEN_KEY = "dtp.token";
const USER_KEY = "dtp.user";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

export function setCachedUser(user: unknown) {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function getCachedUser<T = unknown>(): T | null {
  if (typeof window === "undefined") return null;
  const v = window.localStorage.getItem(USER_KEY);
  return v ? (JSON.parse(v) as T) : null;
}