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

const mobileSameOriginBase =
  typeof window !== "undefined" &&
  (window.location.pathname === "/mobile" || window.location.pathname === "/mobile/")
    ? window.location.origin
    : "";

const configuredApiBase =
  mobileSameOriginBase ||
  (typeof window !== "undefined" && window.__SELENE_API_BASE__) ||
  import.meta.env?.VITE_SELENE_API_BASE ||
  "http://127.0.0.1:8766";

export const API = configuredApiBase.replace(/\/+$/, "");

function mobilePairingHeader(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    const params = new URLSearchParams(window.location.search);
    const fromUrl = params.get("pairing") || params.get("pairing_code") || "";
    if (fromUrl) {
      window.localStorage?.setItem("selene_mobile_pairing", fromUrl);
      params.delete("pairing");
      params.delete("pairing_code");
      const cleanSearch = params.toString();
      window.history.replaceState(
        {},
        document.title,
        `${window.location.pathname}${cleanSearch ? `?${cleanSearch}` : ""}${window.location.hash}`
      );
    }
    const token = fromUrl || window.localStorage?.getItem("selene_mobile_pairing") || "";
    return token ? { "X-Selene-Mobile-Pairing": token } : {};
  } catch {
    return {};
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(path.startsWith("/api/mobile/") ? mobilePairingHeader() : {}),
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
