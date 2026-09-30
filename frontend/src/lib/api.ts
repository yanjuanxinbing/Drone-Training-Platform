// Frontend API client. Talks to the FastAPI backend.

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE?.replace(/\/$/, "") ?? "http://localhost:8000";

let tokenGetter: () => string | null = () => {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem("dtp.token");
};
let tokenClearer: () => void = () => {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem("dtp.token");
  window.localStorage.removeItem("dtp.user");
};

export function configureAuth(getter: () => string | null, clearer: () => void) {
  tokenGetter = getter;
  tokenClearer = clearer;
}

export class ApiException extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

type FetchOptions = RequestInit & { json?: unknown };

async function request<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };

  const token = tokenGetter();
  if (token) headers.Authorization = `Bearer ${token}`;

  let body: BodyInit | undefined;
  if (options.json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(options.json);
  } else {
    body = options.body ?? undefined;
  }

  const url = `${API_BASE}${path}`;
  let resp: Response;
  try {
    resp = await fetch(url, {
      ...options,
      headers,
      body,
      cache: options.cache ?? "no-store",
    });
  } catch (err) {
    throw new ApiException(0, err instanceof Error ? err.message : "网络异常");
  }

  if (resp.status === 401) {
    tokenClearer();
  }

  const text = await resp.text();
  const data = text ? safeJSON(text) : null;

  if (!resp.ok) {
    const detail = (data && (data.detail || data.message)) || resp.statusText;
    throw new ApiException(resp.status, typeof detail === "string" ? detail : "请求失败");
  }
  return data as T;
}

function safeJSON(text: string) {
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export const api = {
  // Auth
  login: (phone: string, password: string) =>
    request<{ access_token: string; user: import("./types").UserPublic; expires_in: number }>(
      "/api/auth/login",
      { method: "POST", json: { phone, password } },
    ),
  register: (phone: string, password: string, confirm_password: string) =>
    request<{ access_token: string; user: import("./types").UserPublic; expires_in: number }>(
      "/api/auth/register",
      { method: "POST", json: { phone, password, confirm_password, agree: true } },
    ),

  // Users
  me: () => request<import("./types").UserPublic>("/api/users/me"),

  // Scenarios
  scenarios: () => request<import("./types").ScenarioList>("/api/scenarios"),
  scenario: (slug: string) =>
    request<import("./types").Scenario>(`/api/scenarios/${slug}`),
  myProgress: () =>
    request<import("./types").ProgressEntry[]>("/api/scenarios/me/progress"),
  saveProgress: (slug: string, body: { score: number; duration_seconds: number; completed: boolean }) =>
    request<import("./types").ProgressEntry>(`/api/scenarios/${slug}/progress`, {
      method: "POST",
      json: { scenario_slug: slug, ...body },
    }),

  // Sim status
  simStatus: () => request<{ airsim_available: boolean }>("/api/sim/status"),

  // Pixel Streaming (UE4.27 + Cirrus) entry point. Mirrors the
  // `PIXEL_STREAMING_URL` constant in test.py at the repo root.
  streamConfig: () =>
    request<{ pixel_streaming_url: string; available: boolean }>(
      "/api/sim/stream-config",
    ),
};

export { API_BASE };