declare global {
  interface Window {
    __SELENE_API_BASE__?: string;
  }

  interface ImportMeta {
    env?: {
      VITE_SELENE_API_BASE?: string;
    };
  }
}

const configuredApiBase =
  (typeof window !== "undefined" && window.__SELENE_API_BASE__) ||
  import.meta.env?.VITE_SELENE_API_BASE ||
  "http://127.0.0.1:8766";

export const API = configuredApiBase.replace(/\/+$/, "");

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {})
    }
  });
  if (!res.ok) {
    let detail = "";
    try {
      const body = await res.json();
      detail = body?.error || body?.message || "";
    } catch {
      detail = "";
    }
    throw new Error(detail ? `${res.status} ${res.statusText}: ${detail}` : `${res.status} ${res.statusText}`);
  }
  return res.json();
}
